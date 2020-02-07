from app import db
import logging

logger = logging.getLogger(__name__)


def create_table_needed(TABLE_NAME, env=None):
    """
    Deletes existing TABLE_NAME if env == test
    Returns True if re-creation of TABLE_NAME needed else returns False
    """

    # Returns first 100 table names
    response = db.client.list_tables(Limit=100)

    # If table exists do not re-create unless env == test
    if TABLE_NAME in response['TableNames']:
        if env == 'test':
            logger.info('{} table already exists. Deleting it since env={}'.format(TABLE_NAME, env))
            response = db.client.delete_table(
                TableName=TABLE_NAME
            )
            waiter = db.client.get_waiter('table_not_exists')
            waiter.wait(TableName=TABLE_NAME)
        else:
            logger.info('{} table already exists. Ignore create request.'.format(TABLE_NAME))
            return False

    return True


def wait_for_table_to_exist(TABLE_NAME):
    # Wait for the table to exist before exiting
    logger.info('Waiting for {} to be created...'.format(TABLE_NAME))
    waiter = db.client.get_waiter('table_exists')
    waiter.wait(TableName=TABLE_NAME)
