import json
from typing import Optional, List

from boto3.dynamodb.conditions import Key
from flask_restplus import abort

from . import PARTITION_KEY
from .model import Account, NewAccount
from .schema import AccountSchema
from ..database.db import DB
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response
from ..shared import getLogger


class AccountService:
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
        if 'accountId' in request_attr:
            account: Account = self.get_by_id(request_attr['accountId'])
            if account is not None:
                request_attr['accountName'] = account.name

        if 'requestedOnResource' in request_attr:
            account: Account = self.get_by_id(request_attr['requestedOnResource'])
            if account is not None:
                request_attr['requestedOnResourceName'] = account.name

    def get_by_user(self, user: CognitoUser) -> Optional[Account]:
        from app import accountsService
        # In order to reduce data size fetched from Dynamodb we have do do this in a round about way.
        # We could do a simple query operation but since data size is calculated before query filter is applied
        # we want to avoid this approach.
        domain = user.email.split('@')[1]
        sameDomainAccounts: List[Account] = accountsService.get_by_domain(domain)
        self.logger.info('Found {} accounts with same domain name for user: {}'.format(
            len(sameDomainAccounts),
            user.email)
        )

        if len(sameDomainAccounts) == 0:
            return None

        accountIdForUser = []
        for account in sameDomainAccounts:
            if user.sub in account.members:
                accountIdForUser.append(account.accountId)

        if len(accountIdForUser) == 0:
            return None

        if len(accountIdForUser) > 1:
            self.logger.error('User found to be member of more than one account: {}'.format(accountIdForUser))
            abort(500, 'Internal Server Error. Please contact support.')

        return self.get_by_id(accountIdForUser[0])

    def get_by_id(self, accountId: str) -> Optional[Account]:
        self.logger.info('AccountService get_by_id called')
        resp = self.table.get_item(
            Key={
                PARTITION_KEY: accountId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)

        if 'Item' in resp:
            self.logger.info('get_by_id: {} returned a Item'.format(accountId))
            return Account(**resp['Item'])
        else:
            self.logger.error('get_by_id: {} not found'.format(accountId))
            return None

    def add_member(self, accountId: str, newMember: str) -> None:
        resp = self.table.update_item(
            Key={
                'accountId': accountId,
            },
            UpdateExpression='set members = list_append(if_not_exists(members, :empty_list), :h)',
            ExpressionAttributeValues={
                ':h': [newMember],
                ':empty_list': []
            },
            ReturnValues='NONE',
        )
        assert_dynamodb_response(resp)

    def update(self, accountId: str, key: str, value: str) -> None:
        self.logger.info('AccountService update called')

        resp = self.table.update_item(
            Key={
                PARTITION_KEY: accountId
            },
            UpdateExpression='set #key = :v',
            ExpressionAttributeValues={':v': value},
            ReturnValues='NONE',
            ExpressionAttributeNames={'#key': key}  # status is reserved Dynamodb keyword hence we have to pass ref #
        )

        self.logger.info(
            'Account update for accountId={} returned update_response: {}'.format(accountId, json.dumps(resp)))

    def owner_account_exists(self, owner: str) -> bool:
        resp = self.table.query(
            IndexName='AccountOwnerIndex',
            KeyConditionExpression=Key('owner').eq(owner),
            Select='COUNT'
        )
        assert_dynamodb_response(resp, 'Count')

        if resp['Count'] == 0:
            return False
        else:
            return True

    def account_by_name_exists(self, name: str) -> bool:
        # Verify that no other account with same name exists
        resp = self.table.query(
            IndexName='AccountNameIndex',
            KeyConditionExpression=Key('name').eq(name),
            Select='COUNT'
        )
        assert_dynamodb_response(resp, 'Count')

        if resp['Count'] == 0:
            return False
        else:
            return True

    def create(self, new_account: NewAccount, cognito_user: CognitoUser = None) -> Optional[Account]:

        self.logger.debug('AccountService create called')

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
        put_response = self.table.put_item(
            Item=new_account_dict
        )
        self.logger.debug('put_response: {}'.format(json.dumps(put_response, indent=4, sort_keys=True)))

        get_response = self.table.get_item(
            Key={
                PARTITION_KEY: str(new_account.accountId)
            },
            ConsistentRead=True
        )

        if 'Item' in get_response:
            persisted_account = get_response['Item']
            return Account(**persisted_account)
        else:
            self.logger.error('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
            return None

    def delete(self, account: Account) -> None:
        try:
            self.logger.debug(
                'AccountService delete called for accountId: {}, accountName: {}'.format(
                    account.accountId,
                    account.name)
            )

            resp = self.table.delete_item(
                Key={
                    'accountId': account.accountId,
                }
            )

            assert_dynamodb_response(resp)
        except Exception as exception:
            self.logger.error('Exception during rollback: {}'.format(exception))
