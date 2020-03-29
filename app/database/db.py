import json

import boto3
import botocore
from boto3 import dynamodb
from botocore.client import BaseClient
from flask_restplus import abort

from app.shared import getLogger


def assert_dynamodb_response(response, expected_attribute=None):
    logger = getLogger(__name__)

    if response is None:
        logger.error('Dynamodb response is None')
        abort(500, message='Internal server error: XN. Please try again.')

    if 'ResponseMetadata' not in response:
        logger.error('Dynamodb response does not contain ResponseMetadata. response = {}'.format(
            json.dumps(response, indent=4, sort_keys=True, default=str)))
        abort(500, message='Internal server error: XR. Please try again.')

    if 'HTTPStatusCode' not in response['ResponseMetadata']:
        logger.error('Dynamodb response does not contain HTTPStatusCode. response = {}'.format(
            json.dumps(response, indent=4, sort_keys=True, default=str)))
        abort(500, message='Internal server error: XH. Please try again.')

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        logger.error('Dynamodb response HTTPStatusCode is not 200. response = {}'.format(
            json.dumps(response, indent=4, sort_keys=True, default=str)))
        abort(500, message='Internal server error: XS. Please try again.')

    if expected_attribute is not None and expected_attribute not in response:
        logger.error('Dynamodb response does not contain expected attribute {}. response = {}'.format(
            expected_attribute, json.dumps(response, indent=4, sort_keys=True, default=str)))
        abort(500, message='Internal server error: XE. Please try again.')


class DB:
    client: botocore.client = None
    dynamodb_resource: dynamodb = None
    stream_client: botocore.client = None

    def init(self, region: str, db_endpoint: str):
        self.client = boto3.client('dynamodb',
                                   region_name=region,
                                   endpoint_url=db_endpoint
                                   )
        self.dynamodb_resource = boto3.resource('dynamodb',
                                                region_name=region,
                                                endpoint_url=db_endpoint
                                                )
        self.stream_client = boto3.client('dynamodbstreams',
                                          region_name=region,
                                          endpoint_url=db_endpoint
                                          )
