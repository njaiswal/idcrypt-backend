from flask_restplus import abort
from app import repoService, accountService
from app.account.model import Account
from app.cognito.cognitoUser import CognitoUser
from app.docs.model import DocPrimaryKeys
from app.repos.model import Repo


class DocAuth:
    def __init__(self, request: DocPrimaryKeys, user: CognitoUser):
        self.newDocRequest: DocPrimaryKeys = request
        self.user: CognitoUser = user

    def doChecks(self):
        """
            - Check account exists
                - Check User is member of account
            - Check repo exists
                - Check User has Repo Access Role
        """
        self.__checkAccount()
        self.__checkRepo()

    def __checkAccount(self):
        account: Account = accountService.get_by_id(self.newDocRequest.accountId)
        if account is None:
            abort(404, message='Account not found.')

        if self.user.sub not in account.members:
            abort(403, message='Not Authorized.')

        self.account: Account = account

    def __checkRepo(self):
        repo: Repo = repoService.get_by_id(self.newDocRequest.accountId, self.newDocRequest.repoId)
        if repo is None:
            abort(404, message='Repository not found.')

        if self.user.sub not in repo.users:
            abort(403, message='Only Account members having Repository Access Role have access to repository.')
        self.repo: Repo = repo
