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

    def init(self, app):
        # Why is this a tuple and not REGION_NAME? todo...
        self.db_endpoint = app.config.get('DYNAMODB_ENDPOINT_URL')[0]
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

        # Create Tables if not exists
        create_tables(env=self.env)
