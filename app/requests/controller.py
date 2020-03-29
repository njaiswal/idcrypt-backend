from datetime import datetime
from typing import List
from flask import request
from flask_accepts import responds, accepts
from flask_restplus import Namespace, Resource
from webargs.flaskparser import use_args
from webargs import fields, validate
from .authz.updateAppRequestAuth import UpdateAppRequestAuth
from .authz.newAppRequestAuth import NewAppRequestAuth
from .model import NewAppRequest, AppRequest, UpdateAppRequest, UpdateHistory
from .schema import AppRequestSchema, NewAppRequestSchema, UpdateAppRequestSchema
from app import requestService, accountsService
from ..account.model import Account
from ..shared import getLogger
from ..utils import get_cognito_user

logger = getLogger(__name__)

api = Namespace(
    name='requests',
    description='Application requests related routes',
)


@api.route("/")
class RequestResource(Resource):
    @use_args({"status": fields.Str(required=False, location="query",
                                    validate=validate.OneOf(["pending", "approved", "denied", "failed", "cancelled", "archived"]))})
    @api.doc(params={'status': 'New status: pending | approved | denied | failed | cancelled | notpending'})
    @responds(schema=AppRequestSchema(many=True))
    def get(self, args: dict) -> List[AppRequest]:
        """Returns requests that a user raised or can approve"""

        cognito_user = get_cognito_user(request)

        requested_status = [None]
        if 'status' in args:
            requested_status = ['approved', 'denied', 'failed', 'cancelled', 'closed'] if args['status'] == 'archived' else [args['status']]

        # First check if user is owner of a account, if yes then return all requests on the account
        my_account: List[Account] = accountsService.get_by_owner(cognito_user.sub)

        foundAppRequests : List[AppRequest] = []
        for status in requested_status:
            if my_account is not None and len(my_account) != 0:
                foundAppRequests += requestService.get_by_accountId(my_account[0].accountId, status=status)
            else:
                # User is not a owner so return all requests initiated by the user
                foundAppRequests += requestService.get_by_requestee(cognito_user.sub, status=status)

        return foundAppRequests

    @accepts(schema=NewAppRequestSchema, api=api)
    @responds(schema=AppRequestSchema)
    def post(self):
        """Submit a request"""
        # Validate with schema
        new_request: NewAppRequest = NewAppRequestSchema().load(api.payload)
        cognito_user = get_cognito_user(request)

        NewAppRequestAuth(new_request, cognito_user).doChecks()

        return requestService.create(cognito_user, new_request)

    @use_args({"status": fields.Str(required=True,
                                    location="query",
                                    validate=validate.OneOf(["approved", "denied", "failed", "cancelled", "closed"]))})
    @accepts(schema=UpdateAppRequestSchema, api=api)
    @responds(schema=AppRequestSchema)
    def put(self, args: dict):
        """Update a request"""
        # Validate with schema
        updateAppRequest: UpdateAppRequest = UpdateAppRequestSchema().load(api.payload)
        cognito_user = get_cognito_user(request)

        # CommonAuth.from_existing_request(updateAppRequest, cognito_user).doChecks()
        UpdateAppRequestAuth(updateAppRequest, cognito_user, args['status']).doChecks()

        #  Update in db
        updateHistory_dict = {'action': args['status'],
                              'updatedBy': cognito_user.sub,
                              'updatedByEmail': cognito_user.email,
                              'updatedAt': str(datetime.now())
                              }
        updateHistory: UpdateHistory = UpdateHistory(**updateHistory_dict)

        requestService.update_status(updateAppRequest, args['status'], updateHistory)

        # Finally return back updated request
        return requestService.get_by_primaryKeys(updateAppRequest.accountId, updateAppRequest.requestId)
