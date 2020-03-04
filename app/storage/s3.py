import os
import tempfile
from typing import List

import boto3
import botocore
from boto3 import s3
from botocore.client import BaseClient

from flask import Flask
from app.account.model import Account
from app.appException import AppException
from app.repos.model import Repo
import logging
from random import randint

logger = logging.getLogger(__name__)


class S3:
    logger = logging.getLogger(__name__)

    client: botocore.client = None
    s3_resource: s3 = None
    s3_endpoint: str = None
    region: str = None
    env: str = None
    loggingBucketName = None

    def init(self, app: Flask):
        self.s3_endpoint = app.config.get('S3_ENDPOINT_URL')
        self.region = app.config.get('REGION_NAME')
        self.env = app.config.get('CONFIG_NAME')
        self.client = boto3.client('s3',
                                   region_name=self.region,
                                   endpoint_url=self.s3_endpoint
                                   )
        self.s3_resource = boto3.resource('s3',
                                          region_name=self.region,
                                          endpoint_url=self.s3_endpoint
                                          )
        self.loggingBucketName = app.config.get('LOGGING_BUCKET_NAME')

    def attemptBucketCreate(self, bucketName) -> str:
        """ Attempts 10 times to create bucket with name=bucketName-xxx where xxxx is random between 1000-9999
            Returns the create bucketName if successful
            raise exception otherwise
        """
        for i in range(10):
            suffix = randint(1000, 9999)
            suffixedBucketName = '{}-{}'.format(bucketName, suffix)
            try:
                self.client.create_bucket(
                    Bucket=suffixedBucketName,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.region
                    }
                )
            except Exception as exception:
                if 'BucketAlreadyExists' in str(exception):
                    logger.error('Seems like bucket name: {} is already taken'.format(bucketName))
                    continue
                else:
                    raise exception
            return suffixedBucketName

        raise AppException('Could not create bucket for account name: {}'.format(bucketName))

    def createRepoBucket(self, account: Account, repo: Repo) -> str:
        bucketName = account.name.replace(' ', '_')
        repoFolderName = repo.name.replace(' ', '_')

        # Create bucket
        self.logger.info('Going to create S3 bucket with name: {}'.format(bucketName))
        createdBucketName = self.attemptBucketCreate(bucketName)

        waiter = self.client.get_waiter('bucket_exists')
        waiter.wait(Bucket=createdBucketName)  # Can wait  5 * 20 = 100 seconds

        # Update bucket logging
        self.logger.info('Going to update S3 bucket: {} logging with target bucket: {}'.format(createdBucketName,
                                                                                               self.loggingBucketName))
        self.client.put_bucket_logging(
            Bucket=createdBucketName,
            BucketLoggingStatus={
                'LoggingEnabled': {
                    'TargetBucket': self.loggingBucketName,
                    'TargetPrefix': '{}/'.format(createdBucketName)
                }
            }
        )

        # Apply server-side encryption on the bucket. This can be later enhanced to start using account specific KMS
        # TODO: Not sure this works. Need to verify in actual S3 setup instead of mocked S3 setup
        self.logger.info('Going to update S3 bucket: {} with default server side encryption'.format(createdBucketName))
        self.client.put_bucket_encryption(
            Bucket=createdBucketName,
            # ContentMD5='string',
            ServerSideEncryptionConfiguration={
                'Rules': [
                    {
                        'ApplyServerSideEncryptionByDefault': {
                            'SSEAlgorithm': 'AES256',
                        }
                    },
                ]
            }
        )

        # Apply a tag to be able to view the cost of this s3 bucket in the bill
        self.logger.info('Going to add a tag to S3 bucket: {}'.format(createdBucketName))
        self.client.put_bucket_tagging(
            Bucket=createdBucketName,
            Tagging={
                'TagSet': [
                    {
                        'Key': 'accountName',
                        'Value': account.name
                    },
                ]
            }
        )

        # Apply lifecycle policy to s3 bucket
        self.logger.info('Going to add lifecycle policy to s3 bucket: {}'.format(createdBucketName))
        self.client.put_bucket_lifecycle_configuration(
            Bucket=createdBucketName,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'Expiration': {
                            'Days': int(repo.retention),
                        },
                        'ID': '{}-lifecyclePolicy'.format(createdBucketName),
                        'Filter': {
                            'Prefix': ''
                        },
                        'Status': 'Enabled',
                        'Transitions': [
                            {
                                'Days': 1,
                                'StorageClass': 'STANDARD_IA'
                            }
                        ],
                        'AbortIncompleteMultipartUpload': {
                            'DaysAfterInitiation': 1
                        }
                    }
                ]
            }
        )

        # Create meta info txt file
        self.logger.info('Going to add info.txt file to s3 bucket within the repo: {}'.format(createdBucketName))
        self.writeRepoMetaInfo(account, repo, createdBucketName)
        return createdBucketName

    def writeRepoMetaInfo(self, account: Account, repo: Repo, bucketName: str):
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                metaInfo: List[str] = [
                    'Account ID: {}'.format(account.accountId),
                    'Account Name: {}'.format(account.name),
                    'Repo Name: {} '.format(repo.name)
                ]
                tmp.writelines(metaInfo)
            repoFolderName = repo.name.replace(' ', '_')
            self.client.upload_file(path, bucketName, '{}/metaInfo.txt'.format(repoFolderName))
        finally:
            os.remove(path)
