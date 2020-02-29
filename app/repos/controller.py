import logging
from typing import List
from flask import request
from flask_accepts import responds
from flask_restplus import Namespace, Resource, abort

from .model import Repo
from .schema import RepoSchema
from .. import repoService, accountService
from ..account.model import Account
from ..utils import get_cognito_user

logger = logging.getLogger(__name__)

api = Namespace(
    name='repos',
    description='Account repositories related routes',
)


@api.route("/")
class RepoResource(Resource):
    @responds(schema=RepoSchema(many=True))
    def get(self) -> List[Repo]:
        """Returns user's account repositories"""

        cognito_user = get_cognito_user(request)
        account: Account = accountService.get_by_user(cognito_user)
        if account is None:
            abort(404, "User's Account not found")

        return repoService.get_by_accountId(account.accountId)

    # @accepts(schema=NewAppRequestSchema, api=api)
    # @responds(schema=AppRequestSchema)
    # def post(self):
    #     """Submit a request"""
    #     # Validate with schema
    #     new_request: NewAppRequest = NewAppRequestSchema().load(api.payload)
    #     cognito_user = get_cognito_user(request)
    #
    #     CommonAuth(new_request, cognito_user).doChecks()
    #     NewAppRequestAuth(new_request, cognito_user).doChecks()
    #
    #     return RequestService.create(cognito_user, new_request)
    #
    # @use_args({"status": fields.Str(required=True,
    #                                 location="query",
    #                                 validate=validate.OneOf(["approved", "denied", "failed", "cancelled", "closed"]))})
    # @accepts(schema=UpdateAppRequestSchema, api=api)
    # @responds(schema=AppRequestSchema)
    # def put(self, args: dict):
    #     """Update a request"""
    #     # Validate with schema
    #     updateAppRequest: UpdateAppRequest = UpdateAppRequestSchema().load(api.payload)
    #     cognito_user = get_cognito_user(request)
    #
    #     # CommonAuth.from_existing_request(updateAppRequest, cognito_user).doChecks()
    #     UpdateAppRequestAuth(updateAppRequest, cognito_user, args['status']).doChecks()
    #
    #     #  Update in db
    #     updateHistory_dict = {'action': args['status'],
    #                           'updatedBy': cognito_user.sub,
    #                           'updatedByEmail': cognito_user.email,
    #                           'updatedAt': str(datetime.now())
    #                           }
    #     updateHistory: UpdateHistory = UpdateHistory(**updateHistory_dict)
    #
    #     RequestService.update_status(updateAppRequest, args['status'], updateHistory)
    #
    #     # Finally return back updated request
    #     return RequestService.get_by_primaryKeys(updateAppRequest.accountId, updateAppRequest.requestId)
