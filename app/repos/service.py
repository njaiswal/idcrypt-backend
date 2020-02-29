import logging
import json
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from flask_restplus import abort
from .model import Repo, NewRepo
from .schema import RepoSchema
from app.database.db import DB
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response


class RepoService:
    logger = logging.getLogger(__name__)

    db = None
    table_name = None
    table = None

    def init(self, db: DB, table_name):
        self.db = db
        self.table_name = table_name
        self.table = db.dynamodb_resource.Table(self.table_name)

    def get_by_id(self, accountId: str, repoId: str) -> Optional[Repo]:
        self.logger.info('RepoService get_by_id called')
        resp = self.table.get_item(
            Key={
                'accountId': accountId,
                'repoId': repoId
            },
            ConsistentRead=True
        )
        assert_dynamodb_response(resp)

        if 'Item' in resp:
            self.logger.info('get_by_id for accountId={}, repoId={} returned an Item'.format(accountId, repoId))
            return Repo(**resp['Item'])
        else:
            self.logger.error('get_by_id for accountId={}, repoId={} returned None'.format(accountId, repoId))
            return None

    # @staticmethod
    # def update(accountId: str, key: str, value: str) -> None:
    #     logger.info('AccountService update called')
    #
    #     resp = table.update_item(
    #         Key={
    #             PARTITION_KEY: accountId
    #         },
    #         UpdateExpression='set {} = :v'.format('#st' if key == 'status' else key),
    #         ExpressionAttributeValues={':v': value},
    #         ReturnValues='NONE',
    #         ExpressionAttributeNames={'#st': 'status'}  # status is reserved Dynamodb keyword
    #     )
    #
    #     logger.info('Account update for accountId={} returned update_response: {}'.format(accountId, json.dumps(resp)))

    # @staticmethod
    # def owner_account_exists(owner: str) -> bool:
    #     resp = table.query(
    #         IndexName='AccountOwnerIndex',
    #         KeyConditionExpression=Key('owner').eq(owner),
    #         Select='COUNT'
    #     )
    #     assert_dynamodb_response(resp, 'Count')
    #
    #     if resp['Count'] == 0:
    #         return False
    #     else:
    #         return True

    def repo_by_name_exists(self, accountId: str, name: str) -> bool:
        """Verify that no other repo with same name exists within the accountId"""
        resp = self.table.query(
            IndexName='AccountIdAndRepoNameIndex',
            KeyConditionExpression=Key('accountId').eq(accountId) & Key('name').eq(name),
            Select='COUNT'
        )
        assert_dynamodb_response(resp, 'Count')

        if resp['Count'] == 0:
            return False
        else:
            return True

    def create(self, accountId: str, new_repo: NewRepo, cognito_user: CognitoUser = None) -> Repo:

        self.logger.debug('RepoService create called')

        new_attrs: dict = {'accountId': accountId,
                           'name': new_repo.name,
                           'desc': new_repo.desc,
                           'retention': new_repo.retention,
                           'users': [cognito_user.sub],
                           'approvers': [cognito_user.sub]
                           }

        repo: Repo = Repo(**new_attrs)

        # Validate with schema
        new_repo_dict = RepoSchema().dump(repo)

        # Create Repo
        put_response = self.table.put_item(
            Item=new_repo_dict
        )
        self.logger.debug('put_response: {}'.format(json.dumps(put_response, indent=4, sort_keys=True)))

        persisted_repo = self.get_by_id(repo.accountId, repo.repoId)
        if persisted_repo is None:
            abort(500, message='Could not create Repo')

        return persisted_repo

    def get_by_accountId(self, accountId: str) -> List[Repo]:
        """Returns all repos for accountId """
        keyConditionExpression = Key('accountId').eq(accountId)

        resp = self.table.query(
            IndexName='AccountIdIndex',
            KeyConditionExpression=keyConditionExpression,
            Select='ALL_ATTRIBUTES'
        )
        assert_dynamodb_response(resp, expected_attribute='Items')

        self.logger.info('get_by_accountId: {} returned {} Items'.format(accountId, len(resp['Items'])))
        found_repos: List[Repo] = []
        for item in resp['Items']:
            found_repos.append(Repo(**item))

        return found_repos
