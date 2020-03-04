from typing import List

from flask_restplus import abort
from app import accountsService, repoService
from app.account.model import Account
from app.cognito.cognitoUser import CognitoUser
from app.repos.model import NewRepo


class NewRepoAuth:
    def __init__(self, request: NewRepo, user: CognitoUser):
        self.newRepoRequest: NewRepo = request
        self.user: CognitoUser = user

    def doChecks(self):
        """
            - User is either a owner or admin of a account
            - Repo name is not duplicate
        """
        self.__checkUserAccount()
        self.__checkRepoNameNotDuplicate()

    def __checkUserAccount(self):
        my_account: List[Account] = accountsService.get_by_owner(self.user.sub)
        if my_account is None or len(my_account) == 0:
            abort(403, 'Only owners and admins of account can create a new repository.')

        # Assuming only one account per owner or admin
        self.myAccount = my_account[0]

    def __checkRepoNameNotDuplicate(self):
        if repoService.repo_by_name_exists(self.myAccount.accountId, self.newRepoRequest.name):
            abort(400, 'Repository with name \'{}\' already exists.'.format(self.newRepoRequest.name))

