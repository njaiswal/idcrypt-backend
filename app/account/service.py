import logging
import json
from typing import Optional

from boto3.dynamodb.conditions import Key
from flask_restplus import abort
from flask_restplus._http import HTTPStatus

from . import PARTITION_KEY
from .model import Account, NewAccount
from .schema import AccountSchema
from app import db
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    def hydrate_request(request_attr: dict):
        if 'accountId' in request_attr:
            account: Account = AccountService.get_by_id(request_attr['accountId'])
            if account is not None:
                request_attr['accountName'] = account.name

        if 'requestedOnResource' in request_attr:
            account: Account = AccountService.get_by_id(request_attr['requestedOnResource'])
            if account is not None:
                request_attr['requestedOnResourceName'] = account.name
            
    @staticmethod
    def get_by_id(accountId: str) -> Optional[Account]:
        table_name = db.table_names['accounts']
        logger.info('AccountService get_by_id called')
        table = db.dynamodb_resource.Table(table_name)
        resp = table.get_item(
            Key={
                PARTITION_KEY: accountId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)

        if 'Item' in resp:
            logger.info('get_by_id: {} returned a Item'.format(accountId))
            return Account(**resp['Item'])
        else:
            logger.error('get_by_id: {} not found'.format(accountId))
            return None

    @staticmethod
    def update(accountId: str, key: str, value: str) -> None:
        table_name = db.table_names['accounts']
        logger.info('AccountService update called')
        table = db.dynamodb_resource.Table(table_name)

        resp = table.update_item(
            Key={
                PARTITION_KEY: accountId
            },
            UpdateExpression='set {} = :v'.format('#st' if key == 'status' else key),
            ExpressionAttributeValues={':v': value},
            ReturnValues='NONE',
            ExpressionAttributeNames={'#st': 'status'}  # status is reserved Dynamodb keyword
        )

        logger.info('Account update for accountId={} returned update_response: {}'.format(accountId, json.dumps(resp)))

    @staticmethod
    def create(new_account: NewAccount, cognito_user: CognitoUser = None) -> Account:
        table_name = db.table_names['accounts']
        logger.debug('AccountService create called')

        new_attrs: dict = {'name': new_account.name,
                           'owner': cognito_user.sub,
                           'email': cognito_user.email,
                           'status': 'active',
                           'tier': 'free'
                           }

        new_account = Account(**new_attrs)

        # Validate with schema
        new_account_dict = AccountSchema().dump(new_account)
        table = db.dynamodb_resource.Table(table_name)

        # Verify that no other account with same name exists
        resp = table.query(
            IndexName='AccountNameIndex',
            KeyConditionExpression=Key('name').eq(new_account.name),
            Select='COUNT'
        )
        if resp['Count'] != 0:
            abort(HTTPStatus.EXPECTATION_FAILED,
                  'Account name \'{}\' already exists. Please choose another name.'.format(new_account.name))

        # Verify that a only one account per-owner can be created
        resp = table.query(
            IndexName='AccountOwnerIndex',
            KeyConditionExpression=Key('owner').eq(new_account.owner),
            Select='COUNT'
        )
        if resp['Count'] != 0:
            abort(HTTPStatus.EXPECTATION_FAILED, 'You are already marked as owner of another account.')

        # Create Account
        put_response = table.put_item(
            Item=new_account_dict
        )
        logger.debug('put_response: {}'.format(json.dumps(put_response, indent=4, sort_keys=True)))

        get_response = table.get_item(
            Key={
                PARTITION_KEY: str(new_account.accountId)
            },
            ConsistentRead=True
        )

        if 'Item' in get_response:
            persisted_account = get_response['Item']
            return persisted_account
        else:
            logger.error('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
