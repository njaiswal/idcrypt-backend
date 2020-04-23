import json
import time

from boto.configservice.exceptions import NoSuchBucketException

from triggers.s3UploadsProcessor import handler, s3, logger
import jinja2

from triggers.helpers.utils import wait_for_port

wait_for_port(port=4500, host='localhost', timeout=60.0)

alreadyProcessed = dict()
uploadBucketName = 'idcrypt-document-uploads172024-test'

i = 0
while True:
    try:
        # Every 3 seconds remove all saved state. This is to allow testing of reused docIds
        if i % 3 is 0:
            alreadyProcessed = dict()

        waiter = s3.client.get_waiter('bucket_exists')
        waiter.wait(Bucket=uploadBucketName)

        uploadBucket = s3.resource.Bucket(uploadBucketName)
        for s3Object in uploadBucket.objects.all():
            if s3Object.key in alreadyProcessed:
                logger.error('Skipping {} since already processed'.format(s3Object.key))
                continue

            logger.info(json.dumps(s3Object, indent=4, sort_keys=True, default=str))
            logger.info('e_tag: {}, last_modified: {}, owner: {}, size: {}, storage_class:{}'.format(s3Object.e_tag,
                                                                                                     s3Object.last_modified,
                                                                                                     s3Object.owner,
                                                                                                     s3Object.size,
                                                                                                     s3Object.storage_class))
            templateLoader = jinja2.FileSystemLoader(searchpath="test-integration/templates")
            templateEnv = jinja2.Environment(loader=templateLoader)
            template = templateEnv.get_template('mockObjectCreatedPutEvent.json')
            outputText = template.render(s3ObjectSummary=s3Object)
            handler(json.loads(outputText), None)
            alreadyProcessed[s3Object.key] = True

        # Sleep 1 second before re-reading the S3 bucket
        time.sleep(1.0)
    except Exception as exp:
        logger.error('Ignoring Exception: {}'.format(exp))
        continue
