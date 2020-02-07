from marshmallow import fields, Schema, validate


class UserSchema(Schema):
    """User schema"""

    userId = fields.String(attribute="userId")
    accountId = fields.String(attribute="accountId")
    firstName = fields.String(attribute="firstName", required=True)
    lastName = fields.String(attribute="lastName", required=True)
    email = fields.Email(attribute="email", required=True)
    status = fields.String(attribute="status", required=True, validate=validate.OneOf(["active", "inactive"]))
    # this should be DateTime. currently not working. todo...
    createdAt = fields.String()

    class Meta:
        fields = ("userId", "accountId", "firstName", "lastName", "email", "status", "createdAt")
        ordered = True
