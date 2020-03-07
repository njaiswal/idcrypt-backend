import logging
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from .model import NewAppRequest, AppRequest, UpdateAppRequest, UpdateHistory
from .schema import AppRequestSchema, UpdateHistorySchema
from app.database.db import DB
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response


class RequestService:
    db = None
    table_name = None
    table = None
    logger = None

    def init(self, db: DB, table_name):
        self.db = db
        self.table_name = table_name
        self.table = db.dynamodb_resource.Table(self.table_name)
        self.logger = logging.getLogger(__name__)

    def get_by_accountId(self, accountId: str, status: str = None):
        """ Returns all requests for a accountID of a particular status if status is present
            Returns all requests for accountID otherwise
        """
        keyConditionExpression = Key('accountId').eq(accountId)
        if status is not None:
            keyConditionExpression = Key('accountId').eq(accountId) & Key('status').eq(status)

        resp = self.table.query(
            IndexName='AccountIdAndStatusIndex',
            KeyConditionExpression=keyConditionExpression,
            Select='ALL_ATTRIBUTES'
        )
        assert_dynamodb_response(resp, expected_attribute='Items')

        self.logger.info('get_by_accountId: {} returned {} Items'.format(accountId, len(resp['Items'])))
        found_app_requests: List[AppRequest] = []
        for item in resp['Items']:
            found_app_requests.append(AppRequest(**item))

        return found_app_requests

    def get_by_requesteeAndRequestType(self, requestee: str, requestType: str = None) -> List[AppRequest]:
        """ Returns all requests made for a user of a particular requestType"""
        # table = db.dynamodb_resource.Table(requests_table_name)

        keyConditionExpression = Key('requestee').eq(requestee) & Key('requestType').eq(requestType)

        resp = self.table.query(
            IndexName='RequesteeAndRequestTypeIndex',
            KeyConditionExpression=keyConditionExpression,
            Select='ALL_ATTRIBUTES'
        )
        assert_dynamodb_response(resp, expected_attribute='Items')

        self.logger.info('get_by_requesteeAndRequestType: {} returned {} Items'.format(requestee, len(resp['Items'])))
        found_app_requests: List[AppRequest] = []
        for item in resp['Items']:
            found_app_requests.append(AppRequest(**item))

        return found_app_requests

    def get_by_requestee(self, requestee: str, status: str = None) -> List[AppRequest]:
        """ Returns all requests made for a user of a particular status if status is present
            Returns all requests made for a user otherwise
        """
        keyConditionExpression = Key('requestee').eq(requestee)
        if status is not None:
            keyConditionExpression = Key('requestee').eq(requestee) & Key('status').eq(status)

        resp = self.table.query(
            IndexName='RequesteeAndStatusIndex',
            KeyConditionExpression=keyConditionExpression,
            Select='ALL_ATTRIBUTES'
        )
        assert_dynamodb_response(resp, expected_attribute='Items')

        self.logger.info('get_by_requestee: {} returned {} Items'.format(requestee, len(resp['Items'])))
        found_app_requests: List[AppRequest] = []
        for item in resp['Items']:
            found_app_requests.append(AppRequest(**item))

        return found_app_requests

    def create(self, cognito_user: CognitoUser, new_request: NewAppRequest) -> AppRequest:
        from app import repoService
        from app import accountService
        from app import idp
        self.logger.debug('create called')

        requesteeSub = None
        if new_request.requesteeEmail is not None:
            requesteeSub = idp.convert_email_to_sub(new_request.requesteeEmail)

        request_attr: dict = {'accountId': new_request.accountId,
                              'requestee': requesteeSub if new_request.requesteeEmail is not None else cognito_user.sub,
                              'requestor': cognito_user.sub,
                              'requesteeEmail': new_request.requesteeEmail if new_request.requesteeEmail is not None else cognito_user.email,
                              'requestorEmail': cognito_user.email,
                              'requestedOnResource': new_request.requestedOnResource,
                              'requestType': new_request.requestType
                              }
        accountService.hydrate_request(request_attr)
        repoService.hydrate_request(request_attr)
        # CognitoService.hydrate_request(request_attr)

        newAppRequest = AppRequest(**request_attr)

        # Validate with schema
        newAppRequest_dict = AppRequestSchema().dump(newAppRequest)
        # table = db.dynamodb_resource.Table(requests_table_name)

        # Create App Request
        response = self.table.put_item(
            Item=newAppRequest_dict
        )
        assert_dynamodb_response(response)
        self.logger.info('App Request with id {} created.'.format(newAppRequest.requestId))

        response = self.table.get_item(
            Key={
                'accountId': str(newAppRequest.accountId),
                'requestId': str(newAppRequest.requestId)
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(response, expected_attribute='Item')

        persisted_request = response['Item']
        return AppRequest(**persisted_request)

    def get_by_primaryKeys(self, accountId: str, requestId: str) -> Optional[AppRequest]:
        """Returns a request with
            Key={
                accountId: ***
                requestId: ***
            }
        """
        resp = self.table.get_item(
            Key={
                'accountId': accountId,
                'requestId': requestId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)

        if 'Item' not in resp:
            self.logger.info('requestId {} does not exist'.format(requestId))
            return None
        else:
            self.logger.info('requestId {} exists'.format(requestId))
            return AppRequest(**resp['Item'])

    def update_status(self, updateAppRequest: UpdateAppRequest, new_status: str, updateHistory: UpdateHistory) -> None:

        resp = self.table.update_item(
            Key={
                'accountId': updateAppRequest.accountId,
                'requestId': updateAppRequest.requestId
            },
            UpdateExpression='set #st = :v, updateHistory = list_append(if_not_exists(updateHistory, :empty_list), :h)',
            ExpressionAttributeValues={
                ':v': new_status,
                ':h': [UpdateHistorySchema().dump(updateHistory)],
                ':empty_list': []
            },
            ReturnValues='NONE',
            ExpressionAttributeNames={'#st': 'status'}  # status is reserved Dynamodb keyword
        )
        assert_dynamodb_response(resp)
