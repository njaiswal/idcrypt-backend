import logging
from enum import Enum
from flask_restplus import abort

from app.account.model import Account
from app.utils import get_cognito_user

logger = logging.getLogger(__name__)


class Action(Enum):
    GET_USER = 1,
    CREATE_USER = 2,
    DELETE_USER = 3,
    GET_ACCOUNT = 4,
    CREATE_ACCOUNT = 5,
    DELETE_ACCOUNT = 6,
    QUERY_ACCOUNTS = 7,
    UPDATE_ACCOUNT = 8


def verify_impersonation(request,
                         action: Action = None,
                         user_id: str = None,
                         payload: dict = None,
                         args=None,
                         account: Account = None) -> None:
    """
    This method is responsible to do authorization.
    Basically what actions authenticated user is allowed to perform on what resources
    """
    cognito_user = get_cognito_user(request)

    if action == Action.GET_USER and cognito_user.username != user_id:
        logger.error('{} cannot impersonate {}'.format(cognito_user.username, user_id))
        abort(403, message='Impersonation not allowed. User: {} cannot get details of another user: {} '.format(
            cognito_user.username, user_id))

    if action == Action.UPDATE_ACCOUNT:
        if account.owner != cognito_user.sub:
            abort(403, message='Only owner of account allowed to update the account.')
