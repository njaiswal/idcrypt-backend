import logging
import json
from typing import List, Optional
from boto3.dynamodb.conditions import Key
from ..database.db import DB
from ..account import PARTITION_KEY
from ..account.model import Account
from ..database.db import assert_dynamodb_response

logger = logging.getLogger(__name__)


class AccountsService:
    db = None
    table_name = None
    table = None

    def init(self, db: DB, table_name):
        self.db = db
        self.table_name = table_name
        self.table = db.dynamodb_resource.Table(self.table_name)

    def get_by_id(self, accountId: str) -> Optional[Account]:
        resp = self.table.get_item(
            Key={
                PARTITION_KEY: accountId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)
        if 'Item' not in resp:
            return None
        return Account(**resp['Item'])

    def get_by_owner(self, owner: str) -> List[Account]:
        resp = self.table.query(
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

    def get_by_domain(self, domain: str) -> List[Account]:
        resp = self.table.query(
            IndexName='AccountDomainIndex',
            KeyConditionExpression=Key('domain').eq(domain),
            Select='ALL_PROJECTED_ATTRIBUTES'
        )
        assert_dynamodb_response(resp)

        same_domain_accounts: List[Account] = []

        if 'Items' in resp:
            logger.info('get_by_domain: {} returned {} Items'.format(domain, len(resp['Items'])))
            for item in resp['Items']:
                account = Account(**item)
                same_domain_accounts.append(account)
        else:
            logger.error('get_by_domain: No Items attribute found. domain={}, Unexpected response: {}'
                         .format(domain, json.dumps(resp, indent=4, sort_keys=True, default=str)))

        return same_domain_accounts

