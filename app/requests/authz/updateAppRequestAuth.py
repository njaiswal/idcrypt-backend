from flask_restplus import abort
from app import accountService, requestService, repoService
from app.account.model import Account
from app.cognito.cognitoUser import CognitoUser
from app.repos.model import Repo
from app.requests.authz.sharedRequestAuth import getResourceType
from app.requests.model import AppRequest, UpdateAppRequest, RequestType
from app.shared import getLogger


class UpdateAppRequestAuth:
    def __init__(self, request: UpdateAppRequest, user: CognitoUser, new_status: str):
        self.request: UpdateAppRequest = request
        self.user: CognitoUser = user
        self.new_status: str = new_status
        self.logger = getLogger(__name__)

    def doChecks(self):
        """
            - Does request exists
            - Is status state change possible. Check integrity of the status change.
            - Does user have appropriate role to change status of request
        """
        self.__checkIfRequestExists()
        self.__statusChangePossible()
        self.__checkIfUserAllowedToChangeStatus()

    def __checkIfRequestExists(self):
        requestInDb: AppRequest = requestService.get_by_primaryKeys(self.request.accountId, self.request.requestId)
        if requestInDb is None:
            abort(404, message='Request not found.')
        self.requestInDb = requestInDb

    def __statusChangePossible(self):
        # Possible status are 'pending', 'approved', 'denied', 'failed', 'cancelled', 'closed'
        #
        #       pending -> cancelled
        #               -> denied
        #               -> approved
        #                           -> closed   (out of band change via requestProcessor)
        #                           -> failed   (out of band change via requestProcessor)
        if self.requestInDb.status == 'pending' and self.new_status in ['cancelled', 'denied', 'approved']:
            pass
        elif self.new_status in ['closed', 'failed']:
            abort(400, message='Users cannot mark requests as {}.'.format(self.new_status))
        elif self.requestInDb.status == self.new_status:
            abort(400, message='Request status already marked as {}.'.format(self.new_status))
        else:
            abort(400, message='Invalid request status change: {}->{}'.format(self.requestInDb.status, self.new_status))

    def __checkIfUserAllowedToChangeStatus(self):
        # For any requestType
        #   Owners, Admins are allowed to mark request as 'approved' or 'denied'
        # For any requestType
        #   Self can mark request as 'cancelled'
        # Repo approvers can only approve, deny doc requests
        # Only worker identity can mark request as 'closed' and 'failed'

        account: Account = accountService.get_by_id(self.request.accountId)
        if account is None:
            abort(404, message='Account not found.')

        # User can only cancel requests if they were the original requestor
        if self.new_status == 'cancelled':
            if self.requestInDb.requestor != self.user.sub:
                abort(403, message='Only requestor can cancel this request.')
            else:
                return

        resourceType = getResourceType(self.requestInDb.requestType)

        # Filter out status types that do not make sense, may be remove them from schema. todo.
        if self.new_status in ['closed', 'failed']:
            abort(500, message='Closed, Failed not implemented yet')

        # If resourceType is account or repo, allow state change by the owner and admins(todo)
        if self.new_status in ['approved', 'denied'] and resourceType in ['account', 'repo']:
            if self.user.sub != account.owner:
                abort(403, message='Not Authorized.')
            else:
                return

        # If resourceType is doc, allow state change by the owner, approvers and admins(todo)
        if self.new_status in ['approved', 'denied'] and resourceType in ['doc']:
            self.repo: Repo = repoService.get_by_id(self.requestInDb.accountId, self.requestInDb.requestedOnResource.split('#')[0])
            if self.user.sub == account.owner or self.user.sub in self.repo.approvers:
                return
            else:
                abort(403, message='Not Authorized.')

        self.logger.error('Cannot decide weather to allow state change. Hence will deny authorization.')
        abort(403, message='Not Authorized')
        # todo: add who can approve deny documentAccess request
        # todo: add who can change status to closed/failed
