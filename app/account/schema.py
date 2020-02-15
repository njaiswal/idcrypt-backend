from marshmallow import fields, Schema, validate, post_load

from app.account.model import NewAccount


class AccountSchema(Schema):
    """Account schema"""

    accountId = fields.String(attribute="accountId")
    name = fields.String(attribute="name", required=True)
    owner = fields.String(attribute="owner")
    domain = fields.String(attribute="domain")
    address = fields.String(attribute="address")
    email = fields.Email(attribute="email")
    status = fields.String(attribute="status", validate=validate.OneOf(["active", "inactive"]))
    tier = fields.String(attribute="tier", validate=validate.OneOf(["free", "enterprise", "dedicated"]))
    # this should be DateTime. currently not working. todo...
    createdAt = fields.String()

    class Meta:
        fields = ("accountId", "name", "owner", "domain", "address", "email", "status", "tier", "createdAt")
        ordered = True


class NewAccountSchema(Schema):
    """New account schema"""
    name = fields.String(attribute="name", required=True, validate=[
        validate.Length(min=3, max=30),
        validate.Regexp(r"^[a-zA-Z0-9_\- ]*$", error="Account name must not contain special characters.")
    ])

    class Meta:
        fields = ["name"]
        ordered = True

    @post_load
    def create_new_account(self, data, **kwarg):
        return NewAccount(**data)
