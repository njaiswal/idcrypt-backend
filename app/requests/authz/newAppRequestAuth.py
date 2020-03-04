import logging
from typing import List
from flask_restplus import abort
from app import accountsService, requestService, repoService, idp
from app.account.model import Account
from app.cognito.cognitoUser import CognitoUser
from app.requests.model import NewAppRequest, AppRequest, RequestType


class NewAppRequestAuth:
    def __init__(self, request: NewAppRequest, user: CognitoUser):
        self.request: NewAppRequest = request
        self.user: CognitoUser = user
        self.logger = logging.getLogger(__name__)
        self.requesteeSub = self.user.sub \
            if self.request.requesteeEmail is None \
            else idp.convert_email_to_sub(self.request.requesteeEmail)

        if self.request.requesteeEmail is not None:
            self.logger.info('Converted email: {} to sub: {}'.format(self.request.requesteeEmail, self.requesteeSub))

    def doChecks(self):
        """
            - Checks if accountId exists
            - Checks if user and onBehalfOf user if exists has or can have relationship with accountId
            - requestedOnResource exists and that resource belongs to the accountId
            - Is request a duplicate
            - Does user have appropriate role to submit this NewAppRequest
            - Checks integrity of the request
        """
        self.__accountExists()
        self.__checkRequester()
        self.__resourceExists()

        self.__checkIfRequestDuplicate()
        self.__checkRequestee()
        self.__checkRequestIntegrity()

    def __accountExists(self):
        account: Account = accountsService.get_by_id(self.request.accountId)
        if account is None:
            abort(404, 'Account ID not found')
        # Cache the account for further checks
        self.account: Account = account

    def __checkRequester(self):
        # joinAccount is special since a non-member can raise joinAccount request
        if self.request.requestType in [
            RequestType.joinAccount.value
        ]:
            user_domain = self.user.email.split('@')[1]
            related_accounts: List[Account] = accountsService.get_by_domain(user_domain)

            user_domain_matches_account_domain = False
            for account in related_accounts:
                if account.accountId == self.request.accountId and account.domain == user_domain:
                    user_domain_matches_account_domain = True
                    break
            if not user_domain_matches_account_domain:
                abort(403, 'User cannot submit a request to join a account with different domain.')

        elif self.request.requestType in [
            RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
            RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
        ]:
            # Make sure that the user is member of the Account or account Owner
            if self.user.sub not in self.account.members and self.user.sub != self.account.owner:
                abort(403, 'Only owner and members of account can raise request of type {}'.format(
                    self.request.requestType))

        else:
            # Check that user is a member/approver/admin/owner of account based on requestType
            abort(400, 'Checks for {} requestType have not yet implemented.'.format(self.request.requestType))

    def __resourceExists(self):
        resourceType = None
        if self.request.requestType in [
            RequestType.joinAccount.value, RequestType.leaveAccount.value
        ]:
            resourceType = 'account'

        if self.request.requestType in [
            RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
            RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
        ]:
            resourceType = 'repo'

        if resourceType is None:
            abort(400, 'Unrecognized requestType ' + self.request.requestType)

        # if resourceType is account just make sure that requestedOnResource == accountId
        # since we already checked accountId exists
        if resourceType == 'account' and self.request.accountId != self.request.requestedOnResource:
            abort(400, 'Malformed payload. Resource does not belong to accountId')

        if resourceType == 'repo':
            self.repo = repoService.get_by_id(self.account.accountId, self.request.requestedOnResource)
            if self.repo is None:
                abort(404, 'Repository not found')

    def __checkIfRequestDuplicate(self):

        existing_matching_requests: List[AppRequest] = requestService.get_by_requesteeAndRequestType(
            self.requesteeSub,
            self.request.requestType
        )

        # Make sure that a joinAccount request is not pending, closed or approved already
        # joinAccount request is special since it can be raised for multiple accountIds
        # Hence we need to do below additional checks
        # A new joinAccount request is only allowed if all previous joinAccount requests have status
        #  - cancel
        #  - denied or
        #  - failed
        # If any other joinAccount request is found say with status
        # - approved
        # - closed
        # - pending
        # Then a new joinAccount request is not allowed
        if self.request.requestType == RequestType.joinAccount.value:
            for joinAccount_request in existing_matching_requests:
                if joinAccount_request.status in ['approved',
                                                  'closed',
                                                  'pending']:
                    message = 'You are already a member of another Account' \
                        if joinAccount_request.status in ['approved', 'closed'] \
                        else 'Similar request already exists. Please cancel it to raise a new one.'
                    abort(400, message=message)
        elif self.request.requestType in [
            RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
            RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
        ]:
            for matching_request in existing_matching_requests:
                if matching_request.status in ['pending']:
                    message = 'Similar request already exists. Please cancel it to raise a new one.'
                    abort(400, message=message)
                else:
                    # We are assuming that these types of requests are idempotent and can be raised again
                    pass
        else:
            abort(400,
                  'Duplicate request check for requestType: {} is not yet implemented'.format(self.request.requestType))

    def __checkRequestee(self):
        # joinAccount request is special since it can be raised by user who is not yet a member of a Account
        if self.request.requestType == RequestType.joinAccount.value:
            # Make sure that owners are not allowed to raise joinAccount request for self
            my_account: List[Account] = accountsService.get_by_owner(self.requesteeSub)
            if my_account is not None and len(my_account) > 0:
                abort(403, 'Owners of account are not allowed to raise join Account requests for self.')
        else:
            if self.requesteeSub not in self.account.members:
                abort(403, 'Only members of account can be requestee for request of type {}'.format(
                    self.request.requestType))

    def __checkRequestIntegrity(self):
        # Owner is always added as repo approver and user roles and it cannot be removed.
        if self.account.owner == self.requesteeSub:
            if self.request.requestType == RequestType.joinAsRepoApprover.value:
                abort(400, message='Owner already has repository approver role.')
            if self.request.requestType == RequestType.grantRepoAccess.value:
                abort(400, message='Owner already has repository user role.')
            if self.request.requestType == RequestType.leaveAsRepoApprover.value:
                abort(400, message='Owner cannot leave repository approver role.')
            if self.request.requestType == RequestType.removeRepoAccess.value:
                abort(400, message='Owner cannot leave repository user role.')

        # Make sure that any leave request is valid
        if self.request.requestType == RequestType.leaveAsRepoApprover.value:
            if self.requesteeSub not in self.repo.approvers:
                abort(400, message='User does not have repository approver role.')

        if self.request.requestType == RequestType.removeRepoAccess.value:
            if self.requesteeSub not in self.repo.users:
                abort(400, message='User does not have repository user role.')
