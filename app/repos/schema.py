from marshmallow import fields, Schema, validate, post_load
from app.account.model import NewRepo
from app.repos.model import Repo


class RepoSchema(Schema):
    """Repo schema"""

    repoId = fields.String(attribute="repoId", required=True)
    accountId = fields.String(attribute="accountId", required=True)
    name = fields.String(attribute="name", required=True)
    desc = fields.String(attribute="desc", required=True)
    retention = fields.Integer(attribute="retention", required=True, validate=[
        validate.Range(min=1, max=1825,
                       error="Retention period of documents in a repository should be between 30 days and 5 years.")
    ])
    approvers = fields.List(fields.String(attribute="approvers", required=True))
    users = fields.List(fields.String(attribute="requestorEmail", required=True))
    createdAt = fields.String(attribute="createdAt", required=True)

    class Meta:
        fields = (
            "repoId",
            "accountId",
            "name",
            "desc",
            "retention",
            "approvers",
            "users",
            "createdAt"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return Repo(**data)


class NewRepoSchema(Schema):
    """New Repository schema"""
    name = fields.String(attribute="name", required=True, validate=[
        validate.Length(min=3, max=30),
        validate.Regexp(r"^[a-zA-Z0-9 ]*$", error="Repo name must not contain special characters.")
    ])

    desc = fields.String(attribute="desc", required=True, validate=[
        validate.Length(min=3, max=30),
        validate.Regexp(r"^[a-zA-Z0-9_\- ]*$", error="Repo description must not contain special characters.")
    ])

    retention = fields.Integer(attribute="retention", required=True, validate=[
        validate.Range(min=30, max=1825,
                       error="Retention period should be between 30 days and 5 years.")
    ])

    class Meta:
        fields = [
            "name",
            "desc",
            "retention"
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return NewRepo(**data)
