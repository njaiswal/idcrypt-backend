import json
from typing import Optional, List
from boto3.dynamodb.conditions import Key
from flask_restplus import abort
from .model import Repo, NewRepo
from .schema import RepoSchema
from app.database.db import DB
from ..cognito.cognitoUser import CognitoUser
from ..database.db import assert_dynamodb_response
from ..shared import getLogger


class RepoService:
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
        if 'requestedOnResource' in request_attr:
            repo: Repo = self.get_by_id(request_attr['accountId'], request_attr['requestedOnResource'])
            if repo is not None:
                request_attr['requestedOnResourceName'] = repo.name

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

    def delete(self, repo: Repo) -> None:
        try:
            self.logger.debug(
                'RepoService delete called for accountId: {}, repoId: {}, repoName: {}'.format(
                    repo.accountId,
                    repo.repoId, repo.name)
            )

            resp = self.table.delete_item(
                Key={
                    'accountId': repo.accountId,
                    'repoId': repo.repoId
                }
            )

            assert_dynamodb_response(resp)
        except Exception as exception:
            self.logger.error('Exception during rollback: {}'.format(exception))

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
        assert_dynamodb_response(put_response)

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

    def add_user(self, accountId: str, repoId: str, newUser: str) -> None:

        repo: Repo = self.get_by_id(accountId, repoId)
        if newUser in repo.users:
            self.logger.error('{} is already a approver on repoName: {}. Ignoring...'.format(newUser, repo.name))
            return

        resp = self.table.update_item(
            Key={
                'accountId': accountId,
                'repoId': repoId
            },
            UpdateExpression='set #u = list_append(if_not_exists(#u, :empty_list), :h)',
            ExpressionAttributeValues={
                ':h': [newUser],
                ':empty_list': []
            },
            ExpressionAttributeNames={'#u': 'users'},  # users is reserved Dynamodb keyword
            ReturnValues='NONE'
        )
        assert_dynamodb_response(resp)

    def add_approver(self, accountId: str, repoId: str, newApprover: str) -> None:

        repo: Repo = self.get_by_id(accountId, repoId)
        if newApprover in repo.approvers:
            self.logger.error('{} is already a approver on repoName: {}. Ignoring...'.format(newApprover, repo.name))
            return

        resp = self.table.update_item(
            Key={
                'accountId': accountId,
                'repoId': repoId
            },
            UpdateExpression='set approvers = list_append(if_not_exists(approvers, :empty_list), :h)',
            ExpressionAttributeValues={
                ':h': [newApprover],
                ':empty_list': []
            },
            ReturnValues='NONE',
        )
        assert_dynamodb_response(resp)

    def remove_approver(self, accountId: str, repoId: str, approver: str) -> None:
        repo: Repo = self.get_by_id(accountId, repoId)

        if approver not in repo.approvers:
            self.logger.error('{} is already NOT a approver on repoName: {}. Ignoring...'.format(approver, repo.name))
            return

        repo.approvers.remove(approver)

        resp = self.table.update_item(
            Key={
                'accountId': accountId,
                'repoId': repoId
            },
            UpdateExpression='set approvers = :h',
            ExpressionAttributeValues={
                ':h': repo.approvers
            },
            ReturnValues='NONE',
        )
        assert_dynamodb_response(resp)

    def remove_user(self, accountId: str, repoId: str, user: str) -> None:
        repo: Repo = self.get_by_id(accountId, repoId)

        if user not in repo.users:
            self.logger.error('{} is already NOT a user on repoName: {}. Ignoring...'.format(user, repo.name))
            return

        repo.users.remove(user)

        resp = self.table.update_item(
            Key={
                'accountId': accountId,
                'repoId': repoId
            },
            UpdateExpression='set #u = :h',
            ExpressionAttributeValues={
                ':h': repo.users
            },
            ExpressionAttributeNames={'#u': 'users'},  # users is reserved Dynamodb keyword
            ReturnValues='NONE',
        )
        assert_dynamodb_response(resp)
