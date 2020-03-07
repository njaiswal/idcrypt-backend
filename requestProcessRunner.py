import json
import socket
import time
from requestProcessor import handler, db, logger


def wait_for_port(port, host='localhost', timeout=60.0):
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


wait_for_port(port=8000, host='localhost', timeout=60.0)

while True:
    tableName = 'Requests-test'
    db.client.get_waiter('table_exists').wait(TableName=tableName)
    table = db.dynamodb_resource.Table(tableName)
    streamArn = table.latest_stream_arn
    # logger.info("Table: {} Stream ARN: {}".format(tableName, streamArn))

    resp = db.stream_client.describe_stream(StreamArn=streamArn)
    # logger.info('Stream desc: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
    # Take the last shard hopefully shards are sorted
    shardId = resp['StreamDescription']['Shards'][-1]['ShardId']
    startingSequenceNumber = resp['StreamDescription']['Shards'][-1]['SequenceNumberRange']['StartingSequenceNumber']
    # logger.info('ShardID: {}'.format(shardId))

    resp = db.stream_client.get_shard_iterator(
        StreamArn=streamArn,
        ShardId=shardId,
        ShardIteratorType='LATEST',
        # SequenceNumber=startingSequenceNumber
    )
    # logger.info('Shard Iterator desc: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
    shard_iterator = resp['ShardIterator']

    # Every 60 seconds refresh the shard_iterator
    # for i in range(0, 60):
    while True:
        try:
            resp = db.stream_client.get_records(
                ShardIterator=shard_iterator,
                Limit=20
            )
            # logger.info('get_records: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
            shard_iterator = resp['NextShardIterator']
            # Call handler if there are Records
            if 'Records' not in resp or len(resp['Records']) > 0:
                handler(resp, None)
            time.sleep(0.01)
        except Exception as exception:
            if 'TrimmedDataAccessException' in str(exception):
                logger.error('Ignoring TrimmedDataAccessException...')
                break
            if 'ExpiredIteratorException' in str(exception):
                logger.error('Ignoring ExpiredIteratorException...')
                break
            else:
                raise exception
