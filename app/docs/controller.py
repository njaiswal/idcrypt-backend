import base64
import os
import tempfile
from typing import List

from flask import request
from flask_accepts import responds, accepts
from flask_restplus import Namespace, Resource

from .authz.docAuth import DocAuth
from .authz.downloadDocAuth import DownloadDocAuth
from .model import Doc, NewDoc, SearchDoc, DownloadDoc, DocImage
from .schema import NewDocSchema, DocSchema, SearchDocSchema, DownloadDocSchema, DocImageSchema
from .. import docService, es, accountService, idp, s3, repoService
from ..account.model import Account
from ..repos.model import Repo
from ..shared import getLogger
from ..storage.s3 import getBucketNameForAccount, getBucketNameForRepo
from ..utils import get_cognito_user
from webargs.flaskparser import use_args
from webargs import fields, validate
import filetype

logger = getLogger(__name__)

api = Namespace(
    name='docs',
    description='Document related routes',
)


@api.route("/")
class DocResource(Resource):
    @use_args(
        {
            "accountId": fields.Str(required=True, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-z0-9-]+$')
            ]),
            "repoId": fields.Str(required=True, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-z0-9-]+$')
            ]),
            "text": fields.Str(required=False, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-zA-Z0-9- ]+$')
            ]),
            "name": fields.Str(required=False, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-zA-Z0-9- ]+$')
            ]),
            "downloadable": fields.Boolean(required=False, location="query")
        })
    @api.doc(params={'accountId': 'Account ID for document search'})
    @api.doc(params={'repoId': 'Repository ID for document search'})
    @api.doc(params={'text': 'Document Text for document search'})
    @api.doc(params={'name': 'Name field for document search'})
    @api.doc(params={'downloadable': 'Boolean'})
    @responds(schema=DocSchema(many=True))
    def get(self, args: dict) -> List[Doc]:
        """Returns documents that match search criteria"""

        # Validate with schema
        searchDoc: SearchDoc = SearchDocSchema().load(args)

        cognito_user = get_cognito_user(request)
        docAuth: DocAuth = DocAuth(searchDoc, cognito_user)
        docAuth.doChecks()

        account: Account = accountService.get_by_id(searchDoc.accountId)
        indexName = 'index-{}'.format(getBucketNameForAccount(account))

        docs: List[Doc] = es.fetch(indexName, searchDoc, cognito_user)

        # Remove data that we do not want to return
        for doc in docs:
            doc.text = None

            # Mark if document is downloadable by user
            doc.downloadable = cognito_user.sub in doc.downloadableBy

            # Hydrate downloadableBy array with email address
            doc.downloadableBy = idp.get_users_by_sub(doc.downloadableBy)

        return docs

    @accepts(schema=NewDocSchema, api=api)
    @responds(schema=DocSchema)
    def post(self) -> Doc:
        """Prepare a New Document Placeholder in given repository"""
        # Validate with schema
        new_doc: NewDoc = NewDocSchema().load(api.payload)
        cognito_user = get_cognito_user(request)

        docAuth: DocAuth = DocAuth(new_doc, cognito_user)
        docAuth.doChecks()

        created_repo: Doc = docService.create(new_doc, cognito_user=cognito_user)
        return created_repo


@api.route("/download")
class DocDownloadResource(Resource):
    @use_args(
        {
            "accountId": fields.Str(required=True, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-z0-9-]+$')
            ]),
            "repoId": fields.Str(required=True, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-z0-9-]+$')
            ]),
            "docId": fields.Str(required=True, location="query", validate=[
                validate.Length(min=3),
                validate.Regexp('^[a-z0-9-]+$')
            ])
        })
    @api.doc(params={'accountId': 'Account ID for document'})
    @api.doc(params={'repoId': 'Repository ID for document'})
    @api.doc(params={'docId': 'Document ID for document'})
    @responds(schema=DocImageSchema)
    def get(self, args: dict) -> DocImage:
        # Validate with schema
        downloadDoc: DownloadDoc = DownloadDocSchema().load(args)
        cognito_user = get_cognito_user(request)

        DocAuth(downloadDoc, cognito_user).doChecks()
        DownloadDocAuth(downloadDoc, cognito_user).doChecks()

        account: Account = accountService.get_by_id(downloadDoc.accountId)
        repo: Repo = repoService.get_by_id(downloadDoc.accountId, downloadDoc.repoId)
        doc: Doc = docService.get_by_id(downloadDoc.repoId, downloadDoc.docId)
        docS3FileName = '{}/{}'.format(getBucketNameForRepo(repo), downloadDoc.docId)

        # Download doc file from s3
        docImage: DocImage = DocImage()
        docImage.name = '{}_{}'.format(doc.name, doc.docType).replace(' ', '_')
        newTmpFile, tempFilePath = tempfile.mkstemp()
        downloadedImageFile = None
        try:
            s3.resource.Bucket(account.bucketName).download_file(docS3FileName, tempFilePath)
            kind = filetype.guess(tempFilePath)
            if kind is not None:
                docImage.name = '{}.{}'.format(docImage.name, kind.extension)
                docImage.contentType = kind.mime
            else:
                logger.error('Could not guess file extension, using jpg instead for repoId: {}, docId:{}'.format(
                    downloadDoc.repoId,
                    downloadDoc.docId)
                )
                docImage.name = '{}.{}'.format(docImage.name, 'jpg')
                docImage.contentType = 'image/jpeg'

            downloadedImageFile = open(tempFilePath, "rb")
            downloadedImageData = downloadedImageFile.read()
            docImage.base64Content = base64.encodebytes(downloadedImageData).decode("utf-8")
        except Exception as exception:
            logger.error('Exception during reading s3 file: {}'.format(exception))
            raise exception
        finally:
            if downloadedImageFile is not None:
                downloadedImageFile.close()
            os.remove(tempFilePath)

        return docImage
