import logging
import json
from typing import List

from boto3.dynamodb.conditions import Key
from flask_restplus import abort
from ..account import PARTITION_KEY
from app import db
from ..account.model import Account, SameDomainAccount
from ..database.db import assert_dynamodb_response

logger = logging.getLogger(__name__)


class AccountsService:
    @staticmethod
    def get_by_id(accountId: str):
        table_name = db.table_names['accounts']
        table = db.dynamodb_resource.Table(table_name)
        get_response = table.get_item(
            Key={
                PARTITION_KEY: accountId
            },
            ConsistentRead=True
        )

        # logger.info('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
        if 'Item' in get_response:
            return get_response['Item']
        else:
            abort(404, 'Account ID not found')

    @staticmethod
    def get_by_owner(owner: str) -> List[Account]:
        table_name = db.table_names['accounts']
        table = db.dynamodb_resource.Table(table_name)
        resp = table.query(
            IndexName='AccountOwnerIndex',
            KeyConditionExpression=Key('owner').eq(owner),
            Select='ALL_PROJECTED_ATTRIBUTES'
        )
        assert_dynamodb_response(resp, expected_attribute='Items')

        logger.info('get_by_owner: {} returned {} Items'.format(owner, len(resp['Items'])))

        my_accounts: List[Account] = []
        for item in resp['Items']:
            my_accounts.append(Account(**item))

        return my_accounts

    @staticmethod
    def get_by_domain(domain: str) -> List[SameDomainAccount]:
        table_name = db.table_names['accounts']
        table = db.dynamodb_resource.Table(table_name)
        resp = table.query(
            IndexName='AccountDomainIndex',
            KeyConditionExpression=Key('domain').eq(domain),
            Select='ALL_PROJECTED_ATTRIBUTES'
        )

        same_domain_accounts: List[SameDomainAccount] = []

        if 'Items' in resp:
            logger.info('get_by_domain: {} returned {} Items'.format(domain, len(resp['Items'])))
            for item in resp['Items']:
                account = SameDomainAccount(**item)
                same_domain_accounts.append(account)
        else:
            logger.error('get_by_domain: No Items attribute found. domain={}, Unexpected response: {}'
                         .format(domain, json.dumps(resp, indent=4, sort_keys=True, default=str)))

        return same_domain_accounts

