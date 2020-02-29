from flask_restplus import abort
from app import accountService
from app.account.model import NewAccount
from app.cognito.cognitoUser import CognitoUser


class NewAccountAuth:
    def __init__(self, request: NewAccount, user: CognitoUser):
        self.newAccountRequest: NewAccount = request
        self.user: CognitoUser = user

    def doChecks(self):
        """
            - Account Name is not duplicate
            - Owner does not own any other accounts
            - todo: User is not associated with any other account as a normal user
        """
        self.__checkAccountName()
        self.__checkOwnerAccounts()

    def __checkAccountName(self):
        if accountService.account_by_name_exists(self.newAccountRequest.name):
            abort(400,
                  'Account name \'{}\' already exists. Please choose another name.'.format(self.newAccountRequest.name))

    def __checkOwnerAccounts(self):
        if accountService.owner_account_exists(self.user.sub):
            abort(400, 'You are already marked as owner of another account.')

    # def __checkRepoName(self):
    #     if RepoService.repo_by_name_exists(self.newAccountRequest.repo.name):
    #         abort(400, 'Repo name \'{}\' already exists. Please choose another name.'.format(
    #             self.newAccountRequest.repo.name))
