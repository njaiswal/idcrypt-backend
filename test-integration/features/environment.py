import logging
import time
import socket

from backend import app
from app import db

logger = logging.getLogger(__name__)


def before_feature(context, feature):
    wait_for_port(port=8000, host='localhost', timeout=60.0)

    app.testing = True
    context.client = app.test_client()


# Deletes all items in table before start of scenario
def before_scenario(context, scenario):
    for (tableName, primaryKey) in [('Accounts-test', 'accountId')]:
        table = db.dynamodb_resource.Table(tableName)
        scan = None

        with table.batch_writer() as batch:
            count = 0
            while scan is None or 'LastEvaluatedKey' in scan:
                if scan is not None and 'LastEvaluatedKey' in scan:
                    scan = table.scan(
                        ProjectionExpression=primaryKey,
                        ExclusiveStartKey=scan['LastEvaluatedKey'],
                    )
                else:
                    scan = table.scan(ProjectionExpression=primaryKey)

                for item in scan['Items']:
                    if count % 5000 == 0:
                        print(count)
                    batch.delete_item(Key={primaryKey: item[primaryKey]})
                    count = count + 1
            logger.info('Deleted {} items from {}'.format(count, tableName))


def wait_for_port(port, host='localhost', timeout=5.0):
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
