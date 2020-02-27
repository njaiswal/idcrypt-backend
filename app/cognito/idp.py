from typing import Optional

import boto3
import botocore
from botocore.client import BaseClient
from flask import Flask
from flask_restplus import abort


class IDP:
    client: botocore.client = None
    region = None
    db_endpoint = None
    env = None
    idp_endpoint = None
    userPoolId = None

    def init(self, app: Flask):
        self.idp_endpoint = app.config.get('IDP_ENDPOINT_URL')
        self.region = app.config.get('REGION_NAME')
        self.env = app.config.get('CONFIG_NAME')
        self.client = boto3.client('cognito-idp',
                                   region_name=self.region,
                                   endpoint_url=self.idp_endpoint
                                   )
        self.userPoolId = app.config.get('COGNITO_USERPOOL_ID')

    def get_user_by_sub(self, sub) -> Optional[dict]:
        resp: dict = self.client.list_users(UserPoolId=self.userPoolId,
                                            # AttributesToGet=[
                                            #
                                            # ],
                                            Limit=1,
                                            Filter='sub="{}"'.format(sub)
                                            )
        if 'Users' not in resp:
            abort(500, message='Internal Server Error. Please try again.')

        if len(resp['Users']) != 1:
            return None

        return resp['Users'][0]

