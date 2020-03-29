import json
from typing import Optional

from flask_restplus import abort
from app.database.db import DB
from .model import NewDoc, Doc, DocStatus
from .schema import DocSchema
from ..account.model import Account
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response

from ..repos.model import Repo
from ..shared import getLogger


class DocService:
    db = None
    table_name = None
    table = None
    logger = None

    def init(self, db: DB, table_name):
        self.db = db
        self.table_name = table_name
        self.table = db.dynamodb_resource.Table(self.table_name)
        self.logger = getLogger(__name__)

    def hydrate_request(self, request_attr: dict):
        from app import repoService
        if 'requestedOnResource' in request_attr and '#' in request_attr['requestedOnResource']:
            parts = request_attr['requestedOnResource'].split('#')
            if len(parts) != 2:
                abort(400, 'Malformed Request Payload')
            repoId = parts[0]
            docId = parts[1]

            repo: Repo = repoService.get_by_id(request_attr['accountId'], repoId)
            doc: Doc = self.get_by_id(repoId, docId)
            if doc is not None:
                request_attr['requestedOnResourceName'] = '{} - {}'.format(repo.name, doc.name)

    def get_by_id(self, repoId: str, docId: str) -> Optional[Doc]:
        self.logger.info('DocService get_by_id called')
        resp = self.table.get_item(
            Key={
                'repoId': repoId,
                'docId': docId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)

        if 'Item' in resp:
            self.logger.info('get_by_id for repoId: {}, docId: {} returned an Item'.format(repoId, docId))
            return Doc(**resp['Item'])
        else:
            self.logger.error('get_by_id for repoId: {}, docId: {} returned None'.format(repoId, docId))
            return None

    def update(self, repoId: str, docId: str, key: str, value: str) -> None:
        self.logger.info('DocService update called')
        resp = self.table.update_item(
            Key={
                'repoId': repoId,
                'docId': docId
            },
            UpdateExpression='set #k = :v',
            ExpressionAttributeValues={':v': value},
            ReturnValues='NONE',
            ExpressionAttributeNames={'#k': key}
        )
        assert_dynamodb_response(resp)

    def add_downloadableBy(self, repoId: str, docId: str, newUser: str) -> None:
        doc: Doc = self.get_by_id(repoId, docId)
        if newUser in doc.downloadableBy:
            self.logger.error(
                '{} is already able to download repoId: {}, docId: {}, docName: {}. Ignoring...'.format(
                    newUser,
                    repoId,
                    docId,
                    doc.name)
            )
            return

        resp = self.table.update_item(
            Key={
                'repoId': repoId,
                'docId': docId
            },
            UpdateExpression='set #u = list_append(if_not_exists(#u, :empty_list), :h)',
            ExpressionAttributeValues={
                ':h': [newUser],
                ':empty_list': []
            },
            ExpressionAttributeNames={'#u': 'downloadableBy'},
            ReturnValues='NONE'
        )
        assert_dynamodb_response(resp)

    def create(self, new_doc: NewDoc, cognito_user: CognitoUser = None) -> Doc:
        from app import repoService
        from app import accountService

        self.logger.debug('DocService create called')
        repo: Repo = repoService.get_by_id(new_doc.accountId, new_doc.repoId)
        account: Account = accountService.get_by_id(new_doc.accountId)

        new_attrs: dict = {'accountId': new_doc.accountId,
                           'repoId': new_doc.repoId,
                           'name': new_doc.name,
                           'retention': repo.retention,
                           'status': DocStatus.initialized.value,
                           'uploadedBy': cognito_user.sub,
                           'downloadableBy': [account.owner],
                           'downloadable': False
                           }

        doc: Doc = Doc(**new_attrs)

        # Validate with schema
        new_doc_dict = DocSchema().dump(doc)

        # Create Doc
        put_response = self.table.put_item(
            Item=new_doc_dict
        )
        self.logger.debug('put_response: {}'.format(json.dumps(put_response, indent=4, sort_keys=True)))
        assert_dynamodb_response(put_response)

        persisted_doc = self.get_by_id(repo.repoId, doc.docId)
        if persisted_doc is None:
            abort(500, message='Could not create Doc')

        return persisted_doc
