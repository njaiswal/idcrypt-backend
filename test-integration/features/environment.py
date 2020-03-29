import logging
import time
import socket

from backend import app
from app import db
from app import s3

logger = logging.getLogger(__name__)


def before_feature(context, feature):
    wait_for_port(port=8000, host='localhost', timeout=60.0)  # Dynamodb server
    wait_for_table_to_exist('Accounts-test')
    wait_for_port(port=4500, host='localhost', timeout=60.0)  # moto s3 server
    wait_for_port(port=9300, host='localhost', timeout=60.0)  # elasticserach server

    app.testing = True
    context.client = app.test_client()


# Deletes all items in table before start of scenario
def before_scenario(context, scenario):
    for (tableName, projectionExpression, hashKey, sortKey) in [
        ('Accounts-test', 'accountId', 'accountId', None),
        ('Requests-test', 'accountId, requestId', 'accountId', 'requestId'),
        ('Repos-test', 'accountId, repoId', 'accountId', 'repoId'),
        ('Docs-test', 'repoId, docId', 'repoId', 'docId')
    ]:
        table = db.dynamodb_resource.Table(tableName)
        scan = None

        with table.batch_writer() as batch:
            count = 0
            while scan is None or 'LastEvaluatedKey' in scan:
                if scan is not None and 'LastEvaluatedKey' in scan:
                    scan = table.scan(
                        ProjectionExpression=projectionExpression,
                        ExclusiveStartKey=scan['LastEvaluatedKey'],
                    )
                else:
                    scan = table.scan(ProjectionExpression=projectionExpression)

                for item in scan['Items']:
                    if sortKey is None:
                        keys = {hashKey: item[hashKey]}
                    else:
                        keys = {hashKey: item[hashKey], sortKey: item[sortKey]}
                    batch.delete_item(Key=keys)
                    count = count + 1
            logger.info('Deleted {} items from {}'.format(count, tableName))

    # Delete all s3 buckets as well
    deletedBuckets = 0
    for bucket in s3.client.list_buckets()['Buckets']:
        bucketResource = s3.resource.Bucket(bucket['Name'])
        bucketResource.objects.all().delete()
        bucketResource.delete()
        deletedBuckets = deletedBuckets + 1
        waiter = s3.client.get_waiter('bucket_not_exists')
        waiter.wait(Bucket=bucket['Name'])

    logger.info('Deleted {} buckets from s3'.format(deletedBuckets))

    # Create upload bucket
    s3.client.create_bucket(
        Bucket='idcrypt-document-uploads-test',
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )
    waiter = s3.client.get_waiter('bucket_exists')
    waiter.wait(Bucket='idcrypt-document-uploads-test')

    # Create upload errors bucket
    s3.client.create_bucket(
        Bucket='idcrypt-upload-errors-test',
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )
    waiter = s3.client.get_waiter('bucket_exists')
    waiter.wait(Bucket='idcrypt-upload-errors-test')

    # Create logging bucket
    s3.client.create_bucket(
        Bucket='idcrypt-s3-access-logs',
        CreateBucketConfiguration={
            'LocationConstraint': 'eu-west-1'
        }
    )
    waiter = s3.client.get_waiter('bucket_exists')
    waiter.wait(Bucket='idcrypt-s3-access-logs')

    # Give the group log-delivery WRITE and READ_ACP permissions to the target logging bucket
    s3.client.put_bucket_acl(
        ACL='log-delivery-write',
        Bucket='idcrypt-s3-access-logs'
    )


def wait_for_port(port, host='localhost', timeout=60.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError('Waited too long for the port {} on host {} to start accepting '
                                   'connections.'.format(port, host)) from ex


def wait_for_table_to_exist(TABLE_NAME):
    # Wait for the table to exist before exiting
    logger.info('Waiting for {} to be created...'.format(TABLE_NAME))
    waiter = db.client.get_waiter('table_exists')
    waiter.wait(TableName=TABLE_NAME)
