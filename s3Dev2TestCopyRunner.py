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
devS3 = S3()
devS3.init(config.REGION_NAME, config.S3_ENDPOINT_URL, config.LOGGING_BUCKET_NAME)

# alreadyProcessed = dict()
testUploadBucketName = 'idcrypt-document-uploads-test'
devUploadBucketName = 'idcrypt-document-uploads172024-dev'

alreadyProcessed = dict()

i = 0
for j in range(0, 10):
    devUploadBucket = devS3.resource.Bucket(devUploadBucketName)

    for devS3Object in devUploadBucket.objects.all():
        if devS3Object.key in alreadyProcessed:
            # logger.error('Skipping {} since already processed'.format(devS3Object.key))
            logger.info('Skipping...')
            continue

        logger.info('Processing: {}'.format(json.dumps(devS3Object, indent=4, sort_keys=True, default=str)))
        newTmpFile, tempFilePath = tempfile.mkstemp()
        devS3.resource.Bucket(devUploadBucketName).download_file(devS3Object.key, tempFilePath)
        s3.resource.Bucket(testUploadBucketName).upload_file(tempFilePath, devS3Object.key)
        alreadyProcessed[devS3Object.key] = True

        logger.info('Copied over: {}'.format(devS3Object.key))

        logger.info('Deleting filename: {} from bucket: {}'.format(devS3Object.key, devUploadBucketName))
        devS3.client.delete_object(Bucket=devUploadBucketName, Key=devS3Object.key)

    # Sleep 10 second before re-reading the S3 bucket
    time.sleep(10.0)
