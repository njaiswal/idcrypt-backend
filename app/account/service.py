import logging
import json
from flask_restplus import abort
from . import TABLE_NAME, PARTITION_KEY
from .model import Account
from .schema import AccountSchema
from app import db

logger = logging.getLogger(__name__)


class AccountService:
    @staticmethod
    def get_by_id(accountId: str):
        logger.info('AccountService get_by_id called')
        table = db.dynamodb_resource.Table(TABLE_NAME)
        get_response = table.get_item(
            Key={
                PARTITION_KEY: accountId
            },
            ConsistentRead=True
        )

        # logger.info('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
        if 'Item' in get_response:
            return get_response['Item']
        else:
            abort(404, 'Account ID not found')

    # @staticmethod
    # def update(account: Account, Widget_change_updates: WidgetInterface) -> Widget:
    #     # widget.update(Widget_change_updates)
    #     # db.session.commit()
    #     print('AccountService update called')
    #     # return widget
    #     return None
    #
    # @staticmethod
    # def delete_by_id(widget_id: int) -> List[int]:
    #     widget = Widget.query.filter(Widget.widget_id == widget_id).first()
    #     if not widget:
    #         return []
    #     db.session.delete(widget)
    #     db.session.commit()
    #     return [widget_id]

    @staticmethod
    def create(new_attrs: dict) -> Account:
        logger.debug('AccountService create called')
        new_account = Account(**new_attrs)

        # Validate with schema
        new_account_dict = AccountSchema().dump(new_account)

        table = db.dynamodb_resource.Table(TABLE_NAME)
        put_response = table.put_item(
            Item=new_account_dict
        )
        logger.debug('put_response: {}'.format(json.dumps(put_response, indent=4, sort_keys=True)))

        get_response = table.get_item(
            Key={
                PARTITION_KEY: str(new_account.accountId)
            },
            ConsistentRead=True
        )

        if 'Item' in get_response:
            persisted_account = get_response['Item']
            return persisted_account
        else:
            logger.error('get_response: {}'.format(json.dumps(get_response, indent=4, sort_keys=True)))
