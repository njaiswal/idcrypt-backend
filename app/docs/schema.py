from marshmallow import fields, Schema, validate, post_load
from app.docs.model import NewDoc, Doc, SearchDoc, DownloadDoc, DocImage


class DocImageSchema(Schema):
    """Doc Image Schema"""
    name = fields.String(attribute="name", required=True)
    base64Content = fields.String(attribute="base64Content", required=True)
    contentType = fields.String(attribute="contentType", required=True)

    class Meta:
        fields = (
            "name",
            "base64Content",
            "contentType"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return DocImage(**data)


class DocSchema(Schema):
    """Doc schema"""
    docId = fields.String(attribute="docId", required=True)
    repoId = fields.String(attribute="repoId", required=True)
    accountId = fields.String(attribute="accountId", required=True)
    retention = fields.Integer(attribute="retention", required=True, validate=[
        validate.Range(min=1, max=1825,
                       error="Retention period of documents in a repository should be between 30 days and 5 years.")
    ])
    status = fields.String(attribute="status", required=True)
    uploadedBy = fields.String(attribute="uploadedBy", required=True)
    uploadedByEmail = fields.String(attribute="uploadedByEmail", required=False)
    downloadableBy = fields.List(fields.String(attribute="downloadableBy", required=True))
    downloadable = fields.Boolean(attribute="downloadable", required=False)
    docType = fields.String(attribute="docType", required=False)
    text = fields.String(attribute="text", required=False)
    name = fields.String(attribute="name", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-zA-Z0-9 ]+$')
    ])
    createdAt = fields.String(attribute="createdAt", required=True)
    errorMessage = fields.String(attribute="errorMessage", required=False)

    class Meta:
        fields = (
            "docId",
            "repoId",
            "accountId",
            "retention",
            "status",
            "uploadedBy",
            "uploadedByEmail",
            "downloadableBy",
            "downloadable",
            "docType",
            "text",
            "name",
            "createdAt",
            "errorMessage"
        )
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return Doc(**data)


class NewDocSchema(Schema):
    """New Doc schema"""
    accountId = fields.String(attribute="accountId", required=True, validate=[
        validate.Length(min=3)
    ])
    repoId = fields.String(attribute="repoId", required=True, validate=[
        validate.Length(min=3)
    ])
    name = fields.String(attribute="name", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-zA-Z0-9 ]+$')
    ])

    class Meta:
        fields = [
            "accountId",
            "repoId",
            "name"
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return NewDoc(**data)


class SearchDocSchema(Schema):
    """Search Doc schema"""
    accountId = fields.String(attribute="accountId", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-z0-9-]+$')
    ])
    repoId = fields.String(attribute="repoId", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-z0-9-]+$')
    ])
    text = fields.String(attribute="text", required=False, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-zA-Z0-9 ]+$')
    ])
    name = fields.String(attribute="name", required=False, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-zA-Z0-9 ]+$')
    ])
    downloadable = fields.Boolean(attribute="downloadable", required=False)

    class Meta:
        fields = [
            "accountId",
            "repoId",
            "text",
            "name",
            "downloadable"
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return SearchDoc(**data)


class DownloadDocSchema(Schema):
    """Download Doc schema"""
    accountId = fields.String(attribute="accountId", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-z0-9-]+$')
    ])
    repoId = fields.String(attribute="repoId", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-z0-9-]+$')
    ])
    docId = fields.String(attribute="docId", required=True, validate=[
        validate.Length(min=3),
        validate.Regexp('^[a-z0-9-]+$')
    ])

    class Meta:
        fields = [
            "accountId",
            "repoId",
            "docId"
        ]
        ordered = True

    @post_load
    def create_new(self, data, **kwarg):
        return DownloadDoc(**data)
