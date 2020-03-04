import logging
from typing import List
from flask import request
from flask_accepts import responds, accepts
from flask_restplus import Namespace, Resource, abort

from .authz.newRepoAuth import NewRepoAuth
from .model import Repo, NewRepo
from .schema import RepoSchema, NewRepoSchema
from .. import repoService, accountService, s3, idp
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

        myRepos = repoService.get_by_accountId(account.accountId)
        idp.hydrateRepos(myRepos)

        return myRepos

    @accepts(schema=NewRepoSchema, api=api)
    @responds(schema=RepoSchema)
    def post(self) -> Repo:
        """Create a Repo"""
        # Validate with schema
        new_repo: NewRepo = NewRepoSchema().load(api.payload)
        cognito_user = get_cognito_user(request)

        newRepoAuth = NewRepoAuth(new_repo, cognito_user)
        newRepoAuth.doChecks()

        created_repo = repoService.create(newRepoAuth.myAccount.accountId, new_repo, cognito_user=cognito_user)
        s3.writeRepoMetaInfo(newRepoAuth.myAccount, created_repo, newRepoAuth.myAccount.bucketName)
        return created_repo

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
