import json
import boto3
import botocore
from botocore.client import BaseClient

from app.shared import getLogger


class TextExtract:
    client: botocore.client = None
    logger = None

    def assert_textract_response(self, response):
        if response is None:
            self.logger.error('Textract response is None')
            raise Exception('Unexpected None response from Textract')

        if 'ResponseMetadata' not in response:
            self.logger.error('Textract response does not contain ResponseMetadata. response = {}'.format(
                json.dumps(response, indent=4, sort_keys=True, default=str)))
            raise Exception('Textract response did not contain ResponseMetadata.')

        if 'HTTPStatusCode' not in response['ResponseMetadata']:
            self.logger.error('Textract response does not contain HTTPStatusCode. response = {}'.format(
                json.dumps(response, indent=4, sort_keys=True, default=str)))
            raise Exception('Textract response did not contain HTTPStatusCode.')

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            self.logger.error('Textract response HTTPStatusCode is not 200. response = {}'.format(
                json.dumps(response, indent=4, sort_keys=True, default=str)))
            raise Exception('Textract response HTTPStatusCode is not 200.')

    def init(self, region: str, textExtract_endpoint: str):
        self.client = boto3.client('textract',
                                   region_name=region,
                                   endpoint_url=textExtract_endpoint
                                   )
        self.logger = getLogger(__name__)
