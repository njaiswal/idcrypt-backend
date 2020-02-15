import logging

from backend import app
from app import db

logger = logging.getLogger(__name__)


def before_feature(context, feature):
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
