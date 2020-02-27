import logging
from http import HTTPStatus
from flask import request
from flask_accepts import accepts, responds
from flask_restplus import Namespace, Resource, abort
from webargs import fields, validate
from webargs.flaskparser import use_args

from .authz.newAccountAuth import NewAccountAuth
from .model import Account, NewAccount
from .schema import AccountSchema, NewAccountSchema
from .service import AccountService
from ..repos.model import Repo
from ..repos.service import RepoService
from ..utils import get_cognito_user
from app import s3

logger = logging.getLogger(__name__)

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

        try:
            created_account: Account = AccountService.create(new_account, cognito_user=cognito_user)
            created_repo: Repo = RepoService.create(created_account.accountId, new_account.repo, cognito_user=cognito_user)
            created_bucket = s3.createRepoBucket(created_account, created_repo)
            AccountService.update(created_account.accountId, 'bucketName', created_bucket)
            return created_account
        except Exception as exception:
            logger.error('Exception during new account creation: {}'.format(exception))
            # todo: rollback
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
        account: Account = AccountService.get_by_id(account_id)
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
            AccountService.update(account_id, k, v)

        # Return updated account back
        return AccountService.get_by_id(account_id)
