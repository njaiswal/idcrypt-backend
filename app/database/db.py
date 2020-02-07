import boto3
import botocore
from boto3 import dynamodb
from botocore.client import BaseClient

from app.db_schema import create_tables


class DB:
    client: botocore.client = None
    dynamodb_resource: dynamodb = None
    region = None
    db_endpoint = None
    env = None
    table_names: dict = {}

    def init(self, app):
        self.db_endpoint = app.config.get('DYNAMODB_ENDPOINT_URL')
        self.region = app.config.get('REGION_NAME')
        self.env = app.config.get('CONFIG_NAME')
        self.client = boto3.client('dynamodb',
                                   region_name=self.region,
                                   endpoint_url=self.db_endpoint
                                   )
        self.dynamodb_resource = boto3.resource('dynamodb',
                                                region_name=self.region,
                                                endpoint_url=self.db_endpoint
                                                )

        # todo: Remove this hack and make it more flexible
        self.table_names['accounts'] = 'Accounts-{}'.format(self.env)
        self.table_names['users'] = 'Users-{}'.format(self.env)

        # Create Tables if not exists
        create_tables(env=self.env)
