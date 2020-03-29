from http import HTTPStatus
from typing import List
from flask import request
from flask_accepts import accepts, responds
from flask_restplus import Namespace, Resource, abort
from webargs import fields, validate
from webargs.flaskparser import use_args
from .authz.newAccountAuth import NewAccountAuth
from .model import Account, NewAccount, AccountMember
from .schema import AccountSchema, NewAccountSchema, AccountMemberSchema
from ..repos.model import Repo
from ..shared import getLogger
from ..utils import get_cognito_user
from app import s3, accountService, repoService, idp

logger = getLogger(__name__)

api = Namespace(
    name='account',
    description='Account Admin related routes',
)


@api.route("/")
class AccountResource(Resource):
    """Account"""

    @accepts(schema=NewAccountSchema, api=api)
    @responds(schema=AccountSchema)
    def post(self):
        """Create a Single Account"""
        # Validate with schema
        new_account_schema = NewAccountSchema()
        new_account: NewAccount = new_account_schema.load(api.payload)

        cognito_user = get_cognito_user(request)

        newAccountAuth: NewAccountAuth = NewAccountAuth(new_account, cognito_user)
        newAccountAuth.doChecks()

        created_account: Account = None
        created_repo: Repo = None
        created_bucket: str = None

        try:
            created_account: Account = accountService.create(new_account, cognito_user=cognito_user)
            created_repo: Repo = repoService.create(created_account.accountId, new_account.repo,
                                                    cognito_user=cognito_user)
            created_bucket = s3.createRepoBucket(created_account, created_repo)
            accountService.update(created_account.accountId, 'bucketName', created_bucket)
            idp.hydrateAccounts([created_account])
            return created_account
        except Exception as exception:
            logger.error('Exception during new account creation: {}'.format(exception))
            logger.error('Initiating rollback...')
            # if createRepoBucket threw exception created_bucket will be None
            if created_bucket is None and created_repo is not None:
                repoService.delete(created_repo)
                accountService.delete(created_account)
            # if exception was raised during creating repo then created_repo will be None
            elif created_repo is None and created_account is not None:
                accountService.delete(created_account)
            abort(500, message='New account creation failed. Please try again.')


@api.route("/<string:account_id>")
@api.param("account_id", "Account ID")
class AccountIdResource(Resource):

    @use_args({"status": fields.Str(required=False, location="query", validate=validate.OneOf(["active", "inactive"]))})
    @api.doc(params={'status': 'New status: active | inactive'})
    @responds(schema=AccountSchema)
    def put(self, args: dict, account_id: str) -> Account:
        """Update Single Account"""

        # Make sure we understand the account update call
        if 'status' not in args:
            abort(HTTPStatus.BAD_REQUEST, 'Invalid account update.')

        # Make sure that the account id is present
        account: Account = accountService.get_by_id(account_id)
        if account is None:
            abort(404, 'Account Id not found.')

        # Make sure that the user can update this account. Only owners can update account
        cognito_user = get_cognito_user(request)
        if account.owner != cognito_user.sub:
            logger.error('Non-Owner {} tried to update accountId: {}, accountName: {}'.format(cognito_user.username,
                                                                                              account.accountId,
                                                                                              account.name))
            abort(403, message='Only owner of account allowed to update the account.')

        # Make sure that its a valid update that changes the state
        if 'status' in args and account.status == args['status']:
            abort(HTTPStatus.BAD_REQUEST, 'Status is already set to {}.'.format(args['status']))

        # Finally do the update one attribute a time
        for k, v in args.items():
            accountService.update(account_id, k, v)

        # Return updated account back
        updated_account = accountService.get_by_id(account_id)
        idp.hydrateAccounts([updated_account])
        return updated_account


@api.route("/<string:account_id>/members")
@api.param("account_id", "Account ID")
class AccountMemberResource(Resource):

    @responds(schema=AccountMemberSchema(many=True))
    def get(self, account_id: str) -> List[AccountMember]:
        """Get Account Members"""

        # Make sure that the account id is present
        account: Account = accountService.get_by_id(account_id)
        if account is None:
            abort(404, 'Account Id not found.')

        # Make sure that the user can get info about account members
        cognito_user = get_cognito_user(request)
        if cognito_user.sub not in account.members:
            abort(403, message='Only members of account allowed to get account membership details.')

        # Return account membership
        account = accountService.get_by_id(account_id)
        repos: List[Repo] = repoService.get_by_accountId(account.accountId)

        accountMembership: List[AccountMember] = []
        for sub in account.members:
            attributes = idp.get_user_by_sub(sub)['Attributes']
            member_attributes = dict()
            for attr in attributes:
                member_attributes[attr['Name']] = attr['Value']
            m = AccountMember(**{
                'email': member_attributes['email'],
                'email_verified': member_attributes['email_verified']
            })
            for repo in repos:
                if sub in repo.users:
                    m.addRepoAccess(repo.name)
                if sub in repo.approvers:
                    m.addRepoApprover(repo.name)
            accountMembership.append(m)

        return accountMembership
