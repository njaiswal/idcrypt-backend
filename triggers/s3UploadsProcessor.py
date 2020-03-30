import json
import os
import tempfile
from typing import Optional, List

from app import DocService
from app.account.model import Account
from app.docs.model import Doc, DocStatus, DocType
from app.repos.model import Repo
from app.storage.s3 import S3, getBucketNameForRepo
from app.database.db import DB
from app.repos.service import RepoService
from app.account.service import AccountService
from app.config import config_by_name
from app.textExtract.textExtract import TextExtract
from app.shared import getLogger

logger = getLogger(__name__)

# Get shared config by env
env = os.getenv('ENV', 'test')
config = config_by_name[env]

# Get upload errors bucket name
uploadErrorsBucketName = config.UPLOAD_ERRORS_BUCKET

# Initialize Dynamodb connections
db = DB()
db.init(config.REGION_NAME, config.DYNAMODB_ENDPOINT_URL)

# Initialize S3 connection
s3 = S3()
s3.init(config.REGION_NAME, config.S3_ENDPOINT_URL, config.LOGGING_BUCKET_NAME)

# Initialize Textract connection
textExtract = TextExtract()
textExtract.init(config.REGION_NAME, config.TEXT_EXTRACT_URL)

# Initialize services
docService: DocService = DocService()
docService.init(db, 'Docs-{}'.format(env))

# requestService: RequestService = RequestService()
# requestService.init(db, 'Requests-{}'.format(env))

accountService: AccountService = AccountService()
accountService.init(db, 'Accounts-{}'.format(env))

repoService: RepoService = RepoService()
repoService.init(db, 'Repos-{}'.format(env))


def handler(event, context):
    if 'Records' not in event or len(event['Records']) == 0:
        logger.error('No Records found in event')
        return

    logger.info("Received event: " + json.dumps(event, indent=4, sort_keys=True, default=str))

    ignoredRecords = 0
    successfullyProcessedRecords = 0
    failedToProcessRecords = 0
    errorsEncountered = []

    for record in event['Records']:
        if record['eventName'] != 'ObjectCreated:Put':
            logger.info('Ignoring {} event'.format(record['eventName']))
            ignoredRecords = ignoredRecords + 1
            continue

        fileName: str = record['s3']['object']['key']
        if not fileName.startswith('private/'):
            logger.error('Expecting a s3 filename starting with private/: {}'.format(fileName))
            failedToProcessRecords = failedToProcessRecords + 1
            continue

        fileNameParts: List[str] = fileName.split('/')
        if len(fileNameParts) != 5:
            logger.error(
                'Expecting 5 parts to s3 filename seperated by "/" i.e. {}, instead got: {}'.format(
                    'LEVEL/COGNITO-IDENTITY/REPOI-D/DOC-ID/DOC-TYPE',
                    fileNameParts)
            )
            failedToProcessRecords = failedToProcessRecords + 1
            continue

        level = fileNameParts[0]
        cognitoIdentity = fileNameParts[1]
        repoId = fileNameParts[2]
        docId = fileNameParts[3]
        docType = fileNameParts[4]

        bucketName = record['s3']['bucket']['name']

        logger.info('Processing s3 record for bucket:{}, level:{}, cognitoIdentity:{}, repoId:{}, docId:{}, docType:{}'.format(
            bucketName,
            level,
            cognitoIdentity,
            repoId,
            docId,
            docType
        ))

        doc = convertRecordToDoc(repoId, docId)

        if doc is None:
            failedToProcessRecords = failedToProcessRecords + 1
            moveFileToErrorBucket(bucketName, fileName)
            continue

        # Do not allow re-upload of same docId, this is bad since it breaks the integrity of data
        if doc.status != DocStatus.initialized.value:
            logger.error(
                'Seems like repoId: {}, docId: {} is being re-uploaded. Stopping this re-upload attempt'.format(
                    doc.repoId, doc.docId))
            failedToProcessRecords = failedToProcessRecords + 1
            moveFileToErrorBucket(bucketName, fileName)
            continue

        # Mark doc as being processed
        docService.update(repoId, docId, 'status', DocStatus.beingProcessed.value)

        # Make sure docType is recognized and update docType
        if DocType.from_str(docType) is None:
            logger.error('Unknown docType: {}'.format(docType))
            docService.update(repoId, docId, 'status', DocStatus.failed.value)
            docService.update(repoId, docId, 'errorMessage', 'Unknown docType: {}'.format(docType))
            failedToProcessRecords = failedToProcessRecords + 1
            moveFileToErrorBucket(bucketName, fileName)
            continue
        else:
            docService.update(repoId, docId, 'docType', docType)

        try:
            # Extract text off the document
            text = extractText(bucketName, fileName)

            # Add the extracted text back into dynamodb
            docService.update(repoId, docId, 'text', text)

            # Move this file to appropriate repository
            moveFileToRepoBucket(bucketName, fileName, doc)

            # Mark status of response as successfullyProcessed
            docService.update(repoId, docId, 'status', DocStatus.successfullyProcessed.value)
            successfullyProcessedRecords = successfullyProcessedRecords + 1
        except Exception as exception:
            logger.error(exception)
            failedToProcessRecords = failedToProcessRecords + 1
            docService.update(repoId, docId, 'status', DocStatus.failed.value)
            docService.update(repoId, docId, 'errorMessage', type(exception).__name__)

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


def extractText(bucketName, fileName) -> Optional[str]:
    newTmpFile, tempFilePath = tempfile.mkstemp()
    blockText: List[str] = []
    try:
        s3.resource.Bucket(bucketName).download_file(fileName, tempFilePath)
        fileBytes = open(tempFilePath, "rb").read()
        resp = textExtract.client.detect_document_text(
            Document={
                'Bytes': fileBytes,
            }
        )
        textExtract.assert_textract_response(resp)
        # logger.info(json.dumps(resp, indent=4, sort_keys=True, default=str))

        # May be we want to skip lines with lower confidence ?
        for block in resp['Blocks']:
            if 'Text' in block:
                if block['BlockType'] == 'LINE':
                    blockText.append('{}\n'.format(block['Text']))
                # else:
                #     blockText.append(block['Text'])

    except Exception as exception:
        # Swallow exceptions during text extraction
        logger.error('Error during text extraction: {}'.format(exception))
        return ' '.join(blockText)
    finally:
        os.remove(tempFilePath)

    return ' '.join(blockText)


def moveFileToRepoBucket(srcBucketName: str, fileName: str, doc: Doc):
    # Get the repo bucket name
    account: Account = accountService.get_by_id(doc.accountId)
    repo: Repo = repoService.get_by_id(doc.accountId, doc.repoId)

    if account is None:
        raise Exception('Could not find account for accountId: {}'.format(doc.accountId))

    if repo is None:
        raise Exception('Could not find repo for accountId: {}, repoId: {}'.format(doc.accountId, doc.repoId))

    copy_source = {
        'Bucket': srcBucketName,
        'Key': fileName
    }
    # Copy it across to repo folder
    destination = '{}/{}'.format(getBucketNameForRepo(repo), doc.docId)

    logger.info('Copying srcBucket: {}, srcFileName:{} to destination {}'.format(srcBucketName,
                                                                                 fileName,
                                                                                 destination))
    s3.client.copy(copy_source, account.bucketName, destination)

    # Delete it from upload folder
    logger.info('Deleting filename: {} from bucket: {}'.format(fileName, srcBucketName))
    s3.client.delete_object(Bucket=srcBucketName, Key=fileName)


def moveFileToErrorBucket(srcBucketName: str, fileName: str):
    try:
        logger.error('Moving bucketName: {}, filename: {} to error bucket: {}'.format(srcBucketName,
                                                                                      fileName,
                                                                                      uploadErrorsBucketName))
        copy_source = {
            'Bucket': srcBucketName,
            'Key': fileName
        }
        # Copy it across to error bucket
        s3.client.copy(copy_source, uploadErrorsBucketName, fileName)

        # Delete it from upload folder
        logger.info('Deleting filename: {} from bucket: {}'.format(fileName, srcBucketName))
        s3.client.delete_object(Bucket=srcBucketName, Key=fileName)
    except Exception as exception:
        logger.error('Caught exception while moving file to error bucket. Ignoring.... {}'.format(str(exception)))
