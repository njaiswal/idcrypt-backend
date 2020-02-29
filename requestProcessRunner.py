import json
import time
from requestProcessor import handler, db, logger

tableName = 'Requests-test'
table = db.dynamodb_resource.Table(tableName)
streamArn = table.latest_stream_arn
logger.info("Table: {} Stream ARN: {}".format(tableName, streamArn))

while True:
    resp = db.stream_client.describe_stream(StreamArn=streamArn)
    logger.info('Stream desc: {}'.format(json.dumps(resp, indent=4, sort_keys=True, default=str)))
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

    # Every 10 seconds refresh the shard_iterator
    for i in range(0, 100):
        resp = db.stream_client.get_records(
            ShardIterator=shard_iterator,
            Limit=1
        )
        shard_iterator = resp['NextShardIterator']
        # Call handler if there are Records
        if 'Records' not in resp or len(resp['Records']) > 0:
            handler(resp, None)
        time.sleep(0.1)
