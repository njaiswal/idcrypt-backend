import logging
import json
from typing import Optional, List

from boto3.dynamodb.conditions import Key
from flask_restplus import abort

from . import PARTITION_KEY
from .model import Account, NewAccount, SameDomainAccount
from .schema import AccountSchema
from app import db
from ..accounts.service import AccountsService
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response

logger = logging.getLogger(__name__)

table_name = db.table_names['accounts']
table = db.dynamodb_resource.Table(table_name)


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
    def get_by_user(user: CognitoUser) -> Optional[Account]:
        # In order to reduce data size fetched from Dynamodb we have do do this in a round about way.
        # We could do a simple query operation but since data size is calculated before query filter is applied
        # we want to avoid this approach.
        domain = user.email.split('@')[1]
        sameDomainAccounts: List[SameDomainAccount] = AccountsService.get_by_domain(domain)

        if len(sameDomainAccounts) == 0:
            return None

        accountIdForUser = []
        for account in sameDomainAccounts:
            if user.sub in account.members:
                accountIdForUser.append(account.accountId)

        if len(accountIdForUser) == 0:
            return None

        if len(accountIdForUser) > 1:
            logger.error('User found to be member of more than one account: {}'.format(accountIdForUser))
            abort(500, 'Internal Server Error. Please contact support.')

        return AccountService.get_by_id(accountIdForUser[0])

    @staticmethod
    def get_by_id(accountId: str) -> Optional[Account]:
        logger.info('AccountService get_by_id called')
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
        logger.info('AccountService update called')

        resp = table.update_item(
            Key={
                PARTITION_KEY: accountId
            },
            UpdateExpression='set #key = :v',
            ExpressionAttributeValues={':v': value},
            ReturnValues='NONE',
            ExpressionAttributeNames={'#key': key}  # status is reserved Dynamodb keyword hence we have to pass ref #
        )

        logger.info('Account update for accountId={} returned update_response: {}'.format(accountId, json.dumps(resp)))

    @staticmethod
    def owner_account_exists(owner: str) -> bool:
        resp = table.query(
            IndexName='AccountOwnerIndex',
            KeyConditionExpression=Key('owner').eq(owner),
            Select='COUNT'
        )
        assert_dynamodb_response(resp, 'Count')

        if resp['Count'] == 0:
            return False
        else:
            return True

    @staticmethod
    def account_by_name_exists(name: str) -> bool:
        # Verify that no other account with same name exists
        resp = table.query(
            IndexName='AccountNameIndex',
            KeyConditionExpression=Key('name').eq(name),
            Select='COUNT'
        )
        assert_dynamodb_response(resp, 'Count')

        if resp['Count'] == 0:
            return False
        else:
            return True

    @staticmethod
    def create(new_account: NewAccount, cognito_user: CognitoUser = None) -> Optional[Account]:

        logger.debug('AccountService create called')

        new_attrs: dict = {'name': new_account.name,
                           'owner': cognito_user.sub,
                           'email': cognito_user.email,
                           'status': 'active',
                           'tier': 'free',
                           'members': [cognito_user.sub],
                           'admins': []
                           }

        new_account = Account(**new_attrs)

        # Validate with schema
        new_account_dict = AccountSchema().dump(new_account)

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
            return Account(**persisted_account)
        else:
            logger.error('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
            return None
