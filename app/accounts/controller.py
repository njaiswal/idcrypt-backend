import logging

from flask import request
from flask_accepts import responds
from flask_restplus import Namespace, Resource
from .. import accountsService
from ..account.model import Account
from ..account.schema import AccountSchema
from ..utils import get_cognito_user

logger = logging.getLogger(__name__)

api = Namespace(
    name='accounts',
    description='Accounts Admin related routes',
)


@api.route("/")
class AccountsResource(Resource):
    @api.response(200, 'Success')
    @responds(schema=AccountSchema(many=True))
    def get(self) -> [Account]:
        """Returns account(s) that a user can either join or is a owner of"""

        cognito_user = get_cognito_user(request)

        # First check if user is owner of a account
        my_account = accountsService.get_by_owner(cognito_user.sub)
        if my_account is not None and len(my_account) != 0:
            return my_account

        # Return all accounts that match user's domain. User can join these accounts.
        return accountsService.get_by_domain(cognito_user.email.split('@')[1])
