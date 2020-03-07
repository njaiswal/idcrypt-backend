from marshmallow import fields, Schema, validate, post_load

from app.account.model import NewAccount, AccountMember
from app.repos.schema import NewRepoSchema


class AccountSchema(Schema):
    """Account schema"""

    accountId = fields.String(attribute="accountId", required=True)
    name = fields.String(attribute="name", required=True)
    owner = fields.String(attribute="owner", required=True)
    domain = fields.String(attribute="domain", required=True)
    address = fields.String(attribute="address")
    email = fields.Email(attribute="email", required=True)
    status = fields.String(attribute="status", required=True, validate=validate.OneOf(["active", "inactive"]))
    tier = fields.String(attribute="tier", required=True, validate=validate.OneOf(["free", "enterprise", "dedicated"]))
    members = fields.List(fields.String(), attribute="members", required=True)
    admins = fields.List(fields.String(), attribute="admins", required=True)

    # this should be DateTime. currently not working. todo...
    createdAt = fields.String(attribute="createdAt", required=True)

    class Meta:
        fields = (
            "accountId", "name", "owner", "domain", "address", "email", "status", "tier", "members", "admins",
            "createdAt")
        ordered = True


class NewAccountSchema(Schema):
    """New account schema"""
    name = fields.String(attribute="name", required=True, validate=[
        validate.Length(min=3, max=30),
        validate.Regexp(r"^[a-zA-Z0-9 ]*$", error="Account name must not contain special characters.")
    ])

    repo = fields.Nested(NewRepoSchema, attribute="repo", required=True)

    class Meta:
        fields = [
            "name",
            "repo",
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return NewAccount(**data)


class AccountMemberSchema(Schema):
    """Account members"""
    email = fields.String(attribute="email", required=True)
    email_verified = fields.String(attribute="email_verified", required=True)
    repoAccess = fields.List(fields.String(), attribute="repoAccess", required=True)
    repoApprover = fields.List(fields.String(), attribute="repoApprover", required=True)

    class Meta:
        fields = [
            "email",
            "email_verified",
            "repoAccess",
            "repoApprover"
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return AccountMember(**data)
