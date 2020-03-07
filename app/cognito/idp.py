import json
import logging
from typing import Optional, List

import boto3
import botocore
from botocore.client import BaseClient
from flask import Flask
from flask_restplus import abort

from app.account.model import Account
from app.repos.model import Repo


class IDP:
    client: botocore.client = None
    region = None
    db_endpoint = None
    env = None
    idp_endpoint = None
    userPoolId = None
    cache = dict()
    logger = None

    def init(self, app: Flask):
        self.idp_endpoint = app.config.get('IDP_ENDPOINT_URL')
        self.region = app.config.get('REGION_NAME')
        self.env = app.config.get('CONFIG_NAME')
        self.client = boto3.client('cognito-idp',
                                   region_name=self.region,
                                   endpoint_url=self.idp_endpoint
                                   )
        self.userPoolId = app.config.get('COGNITO_USERPOOL_ID')
        self.logger = logging.getLogger(__name__)

    def hydrateRepos(self, repos: List[Repo]):
        for repo in repos:
            approverEmailList: List[str] = self.get_users_by_sub(repo.approvers)
            if len(approverEmailList) > 0:
                repo.approvers = approverEmailList

            userEmailList: List[str] = self.get_users_by_sub(repo.users)
            if len(userEmailList) > 0:
                repo.users = userEmailList

    def hydrateAccounts(self, accounts: List[Account]):
        for account in accounts:
            memberEmailList: List[str] = self.get_users_by_sub(account.members)
            if len(memberEmailList) > 0:
                account.members = memberEmailList

            adminEmailList: List[str] = self.get_users_by_sub(account.admins)
            if len(adminEmailList) > 0:
                account.admins = adminEmailList

            ownerEmail: List[str] = self.get_users_by_sub([account.owner])
            if len(ownerEmail) == 1:
                account.owner = ownerEmail[0]

    def get_users_by_sub(self, subs: List[str]) -> List[str]:
        emailIdList: List[str] = []
        for sub in subs:
            user: dict = self.get_user_by_sub(sub)
            if user is not None:
                for attribute in user['Attributes']:
                    if attribute['Name'] == 'email':
                        emailIdList.append(attribute["Value"])

        return emailIdList

    def get_user_by_sub(self, sub) -> Optional[dict]:
        if sub in self.cache:
            self.logger.info('Returning user attributes from cache for sub={}'.format(sub))
            return self.cache[sub]

        # Cache miss
        resp: dict = self.client.list_users(UserPoolId=self.userPoolId,
                                            Limit=1,
                                            Filter='sub="{}"'.format(sub)
                                            )

        # self.logger.info('Cognito-IDP list_users by sub={} returned: {}'.format(sub, json.dumps(resp,
        #                                                                                         indent=4,
        #                                                                                         sort_keys=True,
        #                                                                                         default=str))
        #                  )

        if 'Users' not in resp:
            abort(500, message='Internal Server Error. Please try again.')

        if len(resp['Users']) != 1:
            self.logger.error('Found multiple cognito users with same sub: {}'.format(sub))
            return None

        self.cache[sub] = resp['Users'][0]
        return self.cache[sub]

    def convert_email_to_sub(self, email) -> Optional[str]:
        sub = None
        user = self.get_user_by_email(email)
        if user is not None:
            for attribute in user['Attributes']:
                if attribute['Name'] == 'sub':
                    sub = attribute['Value']
                    break
        return sub

    def get_user_by_email(self, email) -> Optional[dict]:
        if email in self.cache:
            self.logger.info('Returning user attributes from cache for email={}'.format(email))
            return self.cache[email]

        # Cache miss
        resp: dict = self.client.list_users(UserPoolId=self.userPoolId,
                                            Limit=20,
                                            Filter='email="{}"'.format(email)
                                            )

        # self.logger.info('Cognito-IDP list_users by email={} returned: {}'.format(email, json.dumps(resp,
        #                                                                                             indent=4,
        #                                                                                             sort_keys=True,
        #                                                                                             default=str))
        #                  )
        if 'Users' not in resp:
            abort(500, message='Internal Server Error. Please try again.')

        # We can get multiple users with same email address, only one of them might be enabled and verified.
        # Hence we have to filter out the users that are not enabled.
        if len(resp['Users']) == 0:
            return None

        enabledUser = None
        for i in range(len(resp['Users'])):
            user = resp['Users'][i]
            userAttributes = user['Attributes']
            userIsEnabled = False
            for j in range(len(userAttributes)):
                attr = userAttributes[j]
                if attr['Name'] == 'email_verified' and attr['Value'] == 'true':
                    userIsEnabled = True
                    break
            if userIsEnabled:
                enabledUser = user
                break

        self.cache[email] = enabledUser
        return self.cache[email]
