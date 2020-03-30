import json
from typing import List

import boto3
from elasticsearch import RequestsHttpConnection
from elasticsearch_dsl import Index, Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch_dsl.response import Response, Hit
from requests_aws4auth import AWS4Auth

from app.account.service import AccountService
from app.cognito.cognitoUser import CognitoUser
from app.repos.service import RepoService
from app.cognito.idp import IDP
from app.docs.model import Doc, SearchDoc
from app.docs.schema import DocSchema
from app.elasticSearch.ESDoc import ESDoc
from app.shared import getLogger


class ES:
    logger = None
    accountService: AccountService = None
    repoService: RepoService = None
    idp: IDP = None

    def init(self, region: str, es_endpoint: str, accountService: AccountService, repoService: RepoService, idp: IDP):
        service = 'es'
        session = boto3.Session()
        credentials = session.get_credentials()

        awsauth = AWS4Auth(credentials.access_key,
                           credentials.secret_key,
                           region,
                           service,
                           session_token=credentials.token
                           )

        use_ssl = True if es_endpoint.startswith('https') else False

        # Create default connection
        connections.create_connection(
            hosts=[es_endpoint],
            http_auth=awsauth,
            use_ssl=use_ssl,
            connection_class=RequestsHttpConnection,
            timeout=20
        )

        self.logger = getLogger(__name__)
        self.accountService = accountService
        self.repoService = repoService
        self.idp = idp

    def execute(self, esSearch) -> List[Doc]:
        self.logger.info('Going to run following ES query {}'.format(
            json.dumps(esSearch.to_dict(), indent=4, sort_keys=True, default=str))
        )
        # Execute the search
        response: Response = esSearch.execute()

        if not response.success():
            self.logger.error('ES search resulted in failure: {}'.format(response.to_dict()))
            raise Exception('Search resulted in failure')

        self.logger.info('ES query took {} msecs and returned {} hits'.format(response.took, response.hits.total.value))
        self.logger.info('Search result: {}'.format(response.hits))
        hits: List[Hit] = response.hits
        docs: List[Doc] = []
        for h in hits:
            docs.append(self.dehyrate(h))
        return docs

    def ingest(self, doc: Doc, indexName: str):
        # Create index if not exists
        if not Index(indexName).exists():
            self.logger.info('Creating index: {}'.format(indexName))
            ESDoc.init(index=indexName)
        else:
            self.logger.info('{} already exists'.format(indexName))

        docDict = self.hydrate(doc)
        self.logger.info('Going to ingest:')
        for key in docDict:
            if key != 'text':
                self.logger.info('\t{}: {}'.format(key, docDict[key]))
            else:
                self.logger.info('\t{}: ***redacted***'.format(key))

        esDoc: ESDoc = ESDoc(**docDict)
        # set _id to be same as Doc primary key.
        # This means that we can ingest same doc again and again to overwrite stored doc in ES
        esDoc.meta.id = '{}#{}'.format(doc.repoId, doc.docId)

        result = esDoc.save(index=indexName)
        if not result:
            self.logger.error('Could not ingest doc.')
            raise Exception('Could not ingest doc')

    def fetch(self, indexName: str, searchDoc: SearchDoc, user: CognitoUser) -> List[Doc]:
        # Only return results from a particular index
        esSearch = Search(index=indexName)
        esSearch = esSearch[0:100]

        self.logger.info('Index Name:' + indexName)

        # Filter results from repoId
        esSearch = esSearch.filter('term', repoId=searchDoc.repoId)

        # Add full text search on document's name and text field
        if searchDoc.text is not None:
            query = Q('bool',
                      should=[
                          Q("wildcard", name='*{}*'.format(searchDoc.text.lower())),
                          Q("wildcard", text='*{}*'.format(searchDoc.text.lower()))
                      ],
                      minimum_should_match=1
                      )
            esSearch = esSearch.query(query)

        if searchDoc.downloadable:
            esSearch = esSearch.filter('term', downloadableBy=user.sub)

        return self.execute(esSearch)

    def dehyrate(self, hit: Hit) -> Doc:
        hitDict: dict = hit.to_dict()
        for key in ['accountName', 'repoName', 'ingestedAt', 'Meta']:
            hitDict.pop(key, None)
        return Doc(**hitDict)

    def hydrate(self, doc: Doc) -> dict:
        docDict = DocSchema().dump(doc)

        try:
            # Get names for uuid
            docDict['accountName'] = self.accountService.get_by_id(doc.accountId).name
            docDict['repoName'] = self.repoService.get_by_id(doc.accountId, doc.repoId).name
            docDict['uploadedByEmail'] = self.idp.get_users_by_sub([doc.uploadedBy])[0]
        except Exception as exception:
            self.logger.error('Error hydrating document: {}'.format(str(exception)))
            raise ESIngestError('ES could not ingest: repoId: {}, docId: {}'.format(doc.repoId, doc.docId))
        return docDict


class ESIngestError(Exception):
    pass
