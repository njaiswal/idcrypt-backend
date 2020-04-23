import json
import os
import tempfile
import time

from app import S3
from app.config import config_by_name
from triggers.s3UploadsProcessor import s3, logger

from triggers.helpers.utils import wait_for_port

wait_for_port(port=4500, host='localhost', timeout=60.0)

# Get shared config for dev
env = os.getenv('ENV', 'dev')
config = config_by_name[env]

# Get upload errors bucket name
uploadErrorsBucketName = config.UPLOAD_ERRORS_BUCKET

# Initialize S3 connection
cloudS3 = S3()
cloudS3.init(config.REGION_NAME, config.S3_ENDPOINT_URL, config.LOGGING_BUCKET_NAME)

# alreadyProcessed = dict()
localUploadBucketName = 'idcrypt-document-uploads172024-test'
cloudUploadBucketName = 'idcrypt-document-uploads172024-test'

alreadyProcessed = dict()

i = 0
for j in range(0, 100):
    cloudUploadBucket = cloudS3.resource.Bucket(cloudUploadBucketName)

    for cloudS3Object in cloudUploadBucket.objects.all():
        if cloudS3Object.key in alreadyProcessed:
            logger.error('Skipping {} since already processed'.format(cloudS3Object.key))
            continue

        logger.info('Processing: {}'.format(json.dumps(cloudS3Object, indent=4, sort_keys=True, default=str)))
        newTmpFile, tempFilePath = tempfile.mkstemp()
        cloudS3.resource.Bucket(cloudUploadBucketName).download_file(cloudS3Object.key, tempFilePath)
        s3.resource.Bucket(localUploadBucketName).upload_file(tempFilePath, cloudS3Object.key)
        alreadyProcessed[cloudS3Object.key] = True

        logger.info('Copied over: {}'.format(cloudS3Object.key))

    # Sleep 10 second before re-reading the S3 bucket
    time.sleep(10.0)

# Delete all processed files before quiting.
# Deleting files from aws s3 upload bucket will impact textraction if any still remaining to be processed.
# Hence we want to delete as late as possible in this helper script that helps us test uploads locally
for key in alreadyProcessed:
    logger.info('Deleting filename: {} from bucket: {}'.format(key, cloudUploadBucketName))
    cloudS3.client.delete_object(Bucket=cloudUploadBucketName, Key=key)
