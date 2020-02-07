import json

from app import db
import logging
from app.utils import create_table_needed, wait_for_table_to_exist

BASE_ROUTE = "account"
TABLE_NAME = "Accounts"
PARTITION_KEY = "accountId"

logger = logging.getLogger(__name__)


def register_routes(api):
    from .controller import api as account_api

    api.add_namespace(account_api, path=f"/{BASE_ROUTE}")


def create_table(env=None):

    if create_table_needed(TABLE_NAME, env=env):
        # Create the table
        # todo. change to ondemand instead of provisioned throughput to pay as you go instead of pay for provisioned throughput no matter what
        response = db.client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    'AttributeName': PARTITION_KEY,
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': PARTITION_KEY,
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )

        logger.debug('Create table response for {} : {}'.format(TABLE_NAME, json.dumps(response, indent=4, sort_keys=True, default=str)))
        wait_for_table_to_exist(TABLE_NAME)
        logger.info('Created {} table.'.format(TABLE_NAME))
