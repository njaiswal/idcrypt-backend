from typing import List

from flask_restplus import abort

from app.account.model import SameDomainAccount
from app.account.service import AccountService
from app.accounts.service import AccountsService
from app.cognito.cognitoUser import CognitoUser
from app.requests.model import NewAppRequest, AppRequest


class CommonAuth:
    def __init__(self, appRequest: NewAppRequest, user: CognitoUser):
        self.appRequest: NewAppRequest = appRequest
        self.user: CognitoUser = user

    @classmethod
    def from_existing_request(cls, existingRequest: AppRequest, user: CognitoUser):
        newAppRequest = NewAppRequest(existingRequest.accountId,
                                      existingRequest.requestType,
                                      existingRequest.requestedOnResource)
        return cls(newAppRequest, user)

    def doChecks(self):
        """
            - Checks if accountId exists
            - Checks if user and onBehalfOf user if exists has or can have relationship with accountId
            - requestedOnResource exists and that resource belongs to the accountId
        """
        self.__accountExists()
        self.__checkRequester()
        self.__resourceExists()

    def __accountExists(self):
        if AccountService.get_by_id(self.appRequest.accountId) is None:
            abort(404, 'accountId not found')

    def __checkRequester(self):
        # If this is a onBehalfOf request make sure authenticated user has appropriate role
        # If new requests contain requestee it means that it was raised by someone else (requester) for requestee
        if self.appRequest.requestee is not None and self.appRequest.requestee != self.user.sub:
            abort(400, 'onBehalfOf requests are not yet implemented')
        else:
            # joinAccount is special since a non-member can raise joinAccount request
            if self.appRequest.requestType in ['joinAccount']:
                user_domain = self.user.email.split('@')[1]
                related_accounts: List[SameDomainAccount] = AccountsService.get_by_domain(user_domain)

                user_domain_matches_account_domain = False
                for account in related_accounts:
                    if account.accountId == self.appRequest.accountId and account.domain == user_domain:
                        user_domain_matches_account_domain = True
                        break
                if not user_domain_matches_account_domain:
                    abort(403, 'User cannot submit a request to join a account with different domain.')
            else:
                # Check that user is a member/approver/admin/owner of account based on requestType
                abort(400, 'Checks for {} requestType have not yet implemented.'.format(self.appRequest.requestType))

    def __resourceExists(self):
        resourceType = None
        if self.appRequest.requestType in ['joinAccount', 'leaveAccount',
                                           'joinAsAccountAdmin', 'leaveAsAccountAdmin',
                                           'activateAccount', 'deactivateAccount']:
            resourceType = 'account'

        if self.appRequest.requestType in ['joinAsRepoApprover', 'leaveAsRepoApprover',
                                           'grantRepoAccess', 'removeRepoAccess']:
            resourceType = 'repo'

        if resourceType is None:
            abort(400, 'Unrecognized requestType ' + self.appRequest.requestType)

        # if resourceType is account just make sure that requestedOnResource == accountId
        # since we already checked accountId exists
        if resourceType == 'account' and self.appRequest.accountId != self.appRequest.requestedOnResource:
            abort(400, 'Malformed payload. Resource does not belong to accountId')

        if resourceType == 'repo':
            abort(400, 'Repo resource checks are unimplemented')
