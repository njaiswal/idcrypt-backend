from typing import List
from flask_restplus import abort
from app import accountsService, requestService
from app.account.model import Account
from app.cognito.cognitoUser import CognitoUser
from app.requests.model import NewAppRequest, AppRequest


class NewAppRequestAuth:
    def __init__(self, request: NewAppRequest, user: CognitoUser):
        self.request: NewAppRequest = request
        self.user: CognitoUser = user

    def doChecks(self):
        """
            - Is request a duplicate
            - Does user have appropriate role to submit this NewAppRequest
            - Checks integrity of the request
        """
        self.__checkIfRequestDuplicate()
        self.__userCanRaiseThisRequest()
        self.__checkRequestIntegrity()

    def __checkIfRequestDuplicate(self):

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
        if self.request.requestType == 'joinAccount':
            # Make sure that a joinAccount request is not pending, closed or approved already
            users_joinAccount_requests: List[AppRequest] = requestService.get_by_requesteeAndRequestType(
                self.user.sub,
                'joinAccount'
            )

            for joinAccount_request in users_joinAccount_requests:
                if joinAccount_request.status in ['approved',
                                                  'closed',
                                                  'pending']:
                    message = 'You are already a member of another Account' \
                        if joinAccount_request.status in ['approved', 'closed'] \
                        else 'Similar request already exists. Please cancel it to raise a new one.'
                    abort(400,
                          message=message)

        else:
            abort(400,
                  'Duplicate request check for requestType: {} is not yet implemented'.format(self.request.requestType))

    def __userCanRaiseThisRequest(self):

        # First make sure if there is a requestee, i.e. its a request made on behalf of someone
        if self.request.requestee is not None:
            # Make sure that the requestor as appropriate role on the account
            abort(400, 'Requests raised On behalf of someone else is not implemented yet!')

        # joinAccount request is special since it can be raised by user who is not yet a member of a Account
        if self.request.requestType == 'joinAccount':
            # Make sure that owners are not allowed to raise joinAccount request for self
            requestee = self.user.sub if self.request.requestee is None else self.request.requestee
            my_account: List[Account] = accountsService.get_by_owner(requestee)
            if my_account is not None and len(my_account) > 0:
                abort(403, 'Owners of account are not allowed to raise join Account requests for self.')

    def __checkRequestIntegrity(self):
        pass
