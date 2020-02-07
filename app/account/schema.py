from marshmallow import fields, Schema, validate


class AccountSchema(Schema):
    """Account schema"""

    accountId = fields.String(attribute="accountId")
    name = fields.String(attribute="name", required=True)
    address = fields.String(attribute="address")
    email = fields.Email(attribute="email", required=True)
    status = fields.String(attribute="status", required=True, validate=validate.OneOf(["active", "inactive"]))
    tier = fields.String(attribute="tier", required=True, validate=validate.OneOf(["free", "enterprise", "dedicated"]))
    # this should be DateTime. currently not working. todo...
    createdAt = fields.String()

    class Meta:
        fields = ("accountId", "name", "address", "email", "status", "tier", "createdAt")
        ordered = True
