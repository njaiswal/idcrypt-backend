import json
import logging
import os
from datetime import datetime
from typing import Optional

from app.database.db import DB
from app.requests.model import AppRequest, UpdateAppRequest, UpdateHistory, RequestType
from app.requests.service import RequestService
from app.repos.service import RepoService
from app.account.service import AccountService
from app.config import config_by_name

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(lineno)d] %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

# Get shared config by env
env = os.getenv('ENV', 'test')
config = config_by_name[env]

# Initialize Dynamodb connections
db = DB()
db.init(config.REGION_NAME, config.DYNAMODB_ENDPOINT_URL)

# Initialize services
requestService: RequestService = RequestService()
requestService.init(db, 'Requests-{}'.format(env))

accountService: AccountService = AccountService()
accountService.init(db, 'Accounts-{}'.format(env))

repoService: RepoService = RepoService()
repoService.init(db, 'Repos-{}'.format(env))


def handler(event, context):
    if 'Records' not in event or len(event['Records']) == 0:
        logger.error('No Records found in event')
        return

    # logger.info("Received event: " + json.dumps(event, indent=4, sort_keys=True, default=str))

    ignoredRecords = 0
    successfullyProcessedRecords = 0
    failedToProcessRecords = 0
    errorsEncountered = []

    for record in event['Records']:
        if record['eventName'] == 'REMOVE':
            logger.info('Ignoring REMOVE event')
            ignoredRecords = ignoredRecords + 1
            continue

        newImage = record['dynamodb']['NewImage']
        status = newImage['status']['S']
        requestId = newImage['requestId']['S']
        accountId = newImage['accountId']['S']

        logger.info('Start processing accountId: {}, requestId: {}, status: {}'.format(accountId, requestId, status))
        if status != 'approved':
            logger.info('Ignoring since status: {}'.format(status))
            ignoredRecords = ignoredRecords + 1
            continue

        appRequest: AppRequest = convertRecordToRequestObj(record)
        if appRequest is None:
            logger.error('Could not fetch request from DB')
            failedToProcessRecords = failedToProcessRecords + 1
            errorsEncountered.append({'record': record, 'error': 'Could not fetch request from DB'})
            continue

        if appRequest.status != status:
            logger.error(
                'Status of request={} fetched from DB does not match streamed event status={}'.format(
                    appRequest.status,
                    status))
            failedToProcessRecords = failedToProcessRecords + 1
            errorsEncountered.append({'record': record, 'error': 'Record status and request status in DB do not match'})
            markRequestStatus(appRequest.requestId, appRequest.accountId, 'failed')
            continue

        if appRequest.requestType not in [
            RequestType.joinAccount.value,
            RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
            RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
        ]:
            logger.error(
                'Event processor does not know how to handle requests of type: {}'.format(appRequest.requestType))
            failedToProcessRecords = failedToProcessRecords + 1
            errorsEncountered.append({'record': record, 'error': 'requestType cannot be processed'})
            markRequestStatus(appRequest.requestId, appRequest.accountId, 'failed')
            continue

        try:
            # Now based on requestType that got approved, do the needful
            if appRequest.requestType == RequestType.joinAccount.value:
                accountService.add_member(appRequest.requestedOnResource, appRequest.requestee)

            if appRequest.requestType == RequestType.joinAsRepoApprover.value:
                repoService.add_approver(appRequest.accountId, appRequest.requestedOnResource, appRequest.requestee)

            if appRequest.requestType == RequestType.leaveAsRepoApprover.value:
                repoService.remove_approver(appRequest.accountId, appRequest.requestedOnResource, appRequest.requestee)

            if appRequest.requestType == RequestType.grantRepoAccess.value:
                repoService.add_user(appRequest.accountId, appRequest.requestedOnResource, appRequest.requestee)

            if appRequest.requestType == RequestType.removeRepoAccess.value:
                repoService.remove_user(appRequest.accountId, appRequest.requestedOnResource, appRequest.requestee)

            # Mark the request as closed since necessary action has been taken
            logger.info('Successfully actioned request of type: {}'.format(appRequest.requestType))
            markRequestStatus(appRequest.requestId, appRequest.accountId, 'closed')
            successfullyProcessedRecords = successfullyProcessedRecords + 1

        except Exception as exception:
            logger.error(exception)
            failedToProcessRecords = failedToProcessRecords + 1
            markRequestStatus(appRequest.requestId, appRequest.accountId, 'failed')

    logger.info('********** Processed:={}, success={}, failure={}, ignored={}'.format(
        len(event['Records']),
        successfullyProcessedRecords,
        failedToProcessRecords,
        ignoredRecords
    ))

    if len(errorsEncountered) != 0:
        logger.error(json.dumps(errorsEncountered, indent=4, sort_keys=True, default=str))


def markRequestStatus(requestId: str, accountId: str, status: str):
    updateAppRequest: UpdateAppRequest = UpdateAppRequest(**{'accountId': accountId, 'requestId': requestId})
    updateHistory_dict = {'action': status,
                          'updatedBy': '007',
                          'updatedByEmail': 'automation@idcrypt.io',
                          'updatedAt': str(datetime.now())
                          }
    updateHistory: UpdateHistory = UpdateHistory(**updateHistory_dict)
    requestService.update_status(updateAppRequest, status, updateHistory)


def convertRecordToRequestObj(record) -> Optional[AppRequest]:
    keys = record['dynamodb']['Keys']
    requestId = keys['requestId']['S']
    accountId = keys['accountId']['S']

    appRequest: AppRequest = requestService.get_by_primaryKeys(accountId, requestId)
    if appRequest is not None:
        return appRequest
    logger.error('Could not fetch request with accountId:{}, requestId:{} from db. It might have been deleted.'.format(accountId, requestId))
    return None
