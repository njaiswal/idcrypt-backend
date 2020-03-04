from marshmallow import fields, Schema, validate, post_load

from app.requests.model import AppRequest, NewAppRequest, UpdateAppRequest, UpdateHistory, RequestType


class UpdateHistorySchema(Schema):
    action = fields.String(attribute="action", required=True,
                           validate=validate.OneOf(['pending', 'approved', 'denied', 'failed', 'cancelled', 'closed']))
    updatedBy = fields.String(attribute="updatedBy", required=True)
    updatedByEmail = fields.String(attribute="updatedByEmail", required=True)
    updatedAt = fields.String(attribute="updatedAt", required=True)

    class Meta:
        fields = (
            "action",
            "updatedBy",
            "updatedByEmail",
            "updatedAt"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return UpdateHistory(**data)


class AppRequestSchema(Schema):
    """App Request schema"""

    requestId = fields.String(attribute="requestId", required=True)
    accountId = fields.String(attribute="accountId", required=True)
    accountName = fields.String(attribute="accountName", required=True)
    requestee = fields.String(attribute="requestee", required=True)
    requestor = fields.String(attribute="requestor", required=True)
    requesteeEmail = fields.String(attribute="requesteeEmail", required=True)
    requestorEmail = fields.String(attribute="requestorEmail", required=True)
    requestType = fields.String(attribute="requestType", required=True,
                                validate=validate.OneOf(['createAccount', 'suspendAccount', 'deleteAccount',
                                                         'joinAccount', 'leaveAccount',
                                                         'joinAsAccountAdmin', 'leaveAsAccountAdmin',
                                                         'joinAsRepoApprover', 'leaveAsRepoApprover',
                                                         'grantRepoAccess', 'removeRepoAccess']))
    requestedOnResource = fields.String(attribute="requestedOnResource", required=True)
    requestedOnResourceName = fields.String(attribute="requestedOnResourceName", required=True)
    status = fields.String(attribute="status",
                           validate=validate.OneOf(['pending', 'approved', 'denied', 'failed', 'cancelled', 'closed']))
    createdAt = fields.String(attribute="createdAt", required=True)
    updateHistory = fields.List(fields.Nested(UpdateHistorySchema), attribute="updateHistory", required=False)

    class Meta:
        fields = (
            "requestId",
            "accountId",
            "accountName",
            "requestee",
            "requestor",
            "requesteeEmail",
            "requestorEmail",
            "requestType",
            "requestedOnResource",
            "requestedOnResourceName",
            "status",
            "createdAt",
            "updatedAt",
            "updateHistory"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return AppRequest(**data)


class NewAppRequestSchema(Schema):
    """New App Request schema"""

    accountId = fields.String(attribute="accountId", required=True)
    requestType = fields.String(attribute="requestType", required=True,
                                validate=validate.OneOf([
                                    RequestType.joinAccount.value, RequestType.leaveAccount.value,
                                    RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
                                    RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
                                ]))
    requestedOnResource = fields.String(attribute="requestedOnResource", required=True)

    # requesteeEmail is optional since by default requestee and requestor is the same user
    requesteeEmail = fields.String(attribute="requesteeEmail", required=False)

    class Meta:
        fields = (
            "accountId",
            "requestType",
            "requestedOnResource",
            "requesteeEmail"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return NewAppRequest(**data)


class UpdateAppRequestSchema(Schema):
    """Update Request schema"""

    accountId = fields.String(attribute="accountId", required=True)
    requestId = fields.String(attribute="requestId", required=True)

    class Meta:
        fields = (
            "accountId",
            "requestId",
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return UpdateAppRequest(**data)
