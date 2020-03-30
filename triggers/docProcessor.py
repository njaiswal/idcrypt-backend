import json
import os
from typing import Optional

from app.storage.s3 import getBucketNameForAccount
from app.docs.service import DocService
from app.cognito.idp import IDP
from app.account.model import Account
from app.account.service import AccountService
from app.config import config_by_name
from app.database.db import DB
from app.docs.model import Doc, DocStatus
from app.elasticSearch.es import ES
from app.repos.service import RepoService
from app.shared import getLogger

logger = getLogger(__name__)

# Get shared config by env
env = os.getenv('ENV', 'test')
config = config_by_name[env]

# Initialize Dynamodb connections
db = DB()
db.init(config.REGION_NAME, config.DYNAMODB_ENDPOINT_URL)

# Initialize services
docService: DocService = DocService()
docService.init(db, 'Docs-{}'.format(env))

accountService: AccountService = AccountService()
accountService.init(db, 'Accounts-{}'.format(env))

repoService: RepoService = RepoService()
repoService.init(db, 'Repos-{}'.format(env))

idp = IDP()
idp.init(config.REGION_NAME, config.IDP_ENDPOINT_URL, config.COGNITO_USERPOOL_ID)

es = ES()
es.init(config.REGION_NAME, config.ES_ENDPOINT_URL, accountService, repoService, idp)


def handler(event, context):
    if 'Records' not in event or len(event['Records']) == 0:
        logger.error('No Records found in event')
        return

    ignoredRecords = 0
    successfullyProcessedRecords = 0
    failedToProcessRecords = 0
    errorsEncountered = []

    for record in event['Records']:
        docId = None
        repoId = None
        try:
            if record['eventName'] in ['REMOVE']:
                logger.info('Ignoring REMOVE event')
                ignoredRecords = ignoredRecords + 1
                continue

            newImage = record['dynamodb']['NewImage']
            status = newImage['status']['S']
            repoId = newImage['repoId']['S']
            docId = newImage['docId']['S']

            logger.info('Start processing repoId: {}, docId: {}, status: {}'.format(repoId, docId, status))

            # Only try to ingest docs that have been successfully processed or failed due to some reason
            # We want to include failed ones as well since at least the customer name is ingested
            # We want to capture all updates to already indexed docs as well
            if status not in [DocStatus.successfullyProcessed.value, DocStatus.failed.value, DocStatus.indexed.value]:
                logger.info('Ignoring since status: {}'.format(status))
                ignoredRecords = ignoredRecords + 1
                continue

            doc: Doc = convertRecordToDoc(repoId, docId)
            if doc is None:
                logger.error('Could not fetch doc from DB')
                failedToProcessRecords = failedToProcessRecords + 1
                errorsEncountered.append({'record': record, 'error': 'Could not fetch doc from DB'})
                continue

            indexName = getIndexNameForDoc(doc)
            es.ingest(doc, indexName)

            # Mark the request as closed since necessary action has been taken
            logger.info('Successfully actioned doc of status: {}'.format(doc.status))
            successfullyProcessedRecords = successfullyProcessedRecords + 1
            docService.update(doc.repoId, doc.docId, 'status', DocStatus.indexed.value)

        except:
            logger.error("Error processing Record event: " + json.dumps(record, indent=4, sort_keys=True, default=str))
            logger.exception('Ignoring exception...')
            failedToProcessRecords = failedToProcessRecords + 1
            try:
                if repoId is not None and docId is not None:
                    docService.update(repoId, docId, 'status', DocStatus.failed.value)
            except:
                logger.exception('Ignoring exception while updating doc status...')

    logger.info('********** Processed={}, success={}, failure={}, ignored={}'.format(
        len(event['Records']),
        successfullyProcessedRecords,
        failedToProcessRecords,
        ignoredRecords
    ))

    if len(errorsEncountered) != 0:
        logger.error(json.dumps(errorsEncountered, indent=4, sort_keys=True, default=str))


def convertRecordToDoc(repoId, docId) -> Optional[Doc]:
    doc: Doc = docService.get_by_id(repoId, docId)
    if doc is None:
        logger.error('Could not fetch doc for repoId: {}, docId: {}'.format(repoId, docId))

    return doc


def getIndexNameForDoc(doc: Doc) -> str:
    account: Account = accountService.get_by_id(doc.accountId)
    return 'index-{}'.format(getBucketNameForAccount(account))
