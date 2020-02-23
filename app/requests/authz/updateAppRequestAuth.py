from flask_restplus import abort

from app.account.model import Account
from app.account.service import AccountService
from app.cognito.cognitoUser import CognitoUser
from app.requests.model import AppRequest, UpdateAppRequest
from app.requests.service import RequestService


class UpdateAppRequestAuth:
    def __init__(self, request: UpdateAppRequest, user: CognitoUser, new_status: str):
        self.request: UpdateAppRequest = request
        self.user: CognitoUser = user
        self.new_status: str = new_status

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
        requestInDb: AppRequest = RequestService.get_by_primaryKeys(self.request.accountId, self.request.requestId)
        if requestInDb is None:
            abort(404, message='Request not found.')
        self.requestInDb = requestInDb

    def __statusChangePossible(self):
        # Possible status are 'pending', 'approved', 'denied', 'failed', 'cancelled', 'closed'
        #
        #       pending -> cancelled
        #               -> denied
        #               -> approved
        #                           -> closed
        #                           -> failed

        if self.requestInDb.status == self.new_status:
            abort(400, message='Request status already marked as {}.'.format(self.new_status))

        if self.requestInDb.status == 'pending' and self.new_status in ['cancelled', 'denied', 'approved']:
            pass
        elif self.requestInDb.status == 'approved' and self.new_status in ['closed', 'failed']:
            pass
        else:
            abort(400, message='Invalid request status change: {}->{}'.format(self.requestInDb.status, self.new_status))

    def __checkIfUserAllowedToChangeStatus(self):
        # For any requestType
        #   Owners, Admins are allowed to mark request as 'approved' or 'denied'
        # For any requestType
        #   Self can mark request as 'cancelled'
        # Repo approvers can only approve, deny doc requests
        # Only worker identity can mark request as 'closed' and 'failed'

        account: Account = AccountService.get_by_id(self.request.accountId)
        if account is None:
            abort(404, message='Account not found.')

        # User can only cancel requests if they were the original requestor
        if self.new_status == 'cancelled':
            if self.requestInDb.requestor != self.user.sub:
                abort(403, message='Only requestor can cancel this request.')

        if self.new_status in ['approved', 'denied']:
            if self.user.sub != account.owner:
                #or self.user.sub in account.admins todo
                abort(403, message='Not Authorized.')

        # todo: add who can approve deny documentAccess request
        # todo: add who can change status to closed/failed
        if self.new_status in ['closed', 'failed']:
            abort(500, message='Closed, Failed not implemented yet')
