import argparse
import importlib
import time

from triggers.helpers.utils import wait_for_port

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--tableName', required=True, help='Table name to stream from')
parser.add_argument('-l', '--labmda', required=True, help='Lambda handler name. e.g.: triggers.requestProcessor')

args = parser.parse_args()

# Import the lambda module
lambdaModule = importlib.import_module(args.labmda)

# Wait for dynamodb to start
wait_for_port(port=8000, host='localhost', timeout=60.0)

while True:
    lambdaModule.db.client.get_waiter('table_exists').wait(TableName=args.tableName)
    table = lambdaModule.db.dynamodb_resource.Table(args.tableName)
    streamArn = table.latest_stream_arn
    # logger.info("Table: {} Stream ARN: {}".format(tableName, streamArn))

    resp = lambdaModule.db.stream_client.describe_stream(StreamArn=streamArn)
    # logger.info('Stream desc: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
    # Take the last shard hopefully shards are sorted
    shardId = resp['StreamDescription']['Shards'][-1]['ShardId']
    startingSequenceNumber = resp['StreamDescription']['Shards'][-1]['SequenceNumberRange']['StartingSequenceNumber']
    # logger.info('ShardID: {}'.format(shardId))

    resp = lambdaModule.db.stream_client.get_shard_iterator(
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
            resp = lambdaModule.db.stream_client.get_records(
                ShardIterator=shard_iterator,
                Limit=20
            )
            # logger.info('get_records: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
            shard_iterator = resp['NextShardIterator']
            # Call handler if there are Records
            if 'Records' not in resp or len(resp['Records']) > 0:
                lambdaModule.handler(resp, None)
            time.sleep(0.25)
        except Exception as exception:
            if 'TrimmedDataAccessException' in str(exception):
                lambdaModule.logger.error('Ignoring TrimmedDataAccessException...')
                break
            if 'ExpiredIteratorException' in str(exception):
                lambdaModule.logger.error('Ignoring ExpiredIteratorException...')
                break
            else:
                raise exception
