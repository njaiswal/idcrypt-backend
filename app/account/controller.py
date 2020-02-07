from flask import request
from flask_accepts import accepts, responds
from flask_restplus import Namespace, Resource
from .model import Account
from .schema import AccountSchema
from .service import AccountService

api = Namespace(
    name='account',
    description='Account Admin related routes',
)


@api.route("/")
class AccountResource(Resource):
    """Account"""

    @accepts(schema=AccountSchema, api=api)
    @responds(schema=AccountSchema)
    def post(self):
        """Create a Single Account"""

        return AccountService.create(request.parsed_obj)


@api.route("/<string:account_id>")
@api.param("account_id", "Account ID")
class AccountIdResource(Resource):
    @responds(schema=AccountSchema)
    def get(self, account_id: str) -> Account:
        """Get Single Account"""

        return AccountService.get_by_id(account_id)

    # def delete(self, widgetId: int) -> Response:
    #     """Delete Single Widget"""
    #     from flask import jsonify
    #
    #     id = WidgetService.delete_by_id(widgetId)
    #     return jsonify(dict(status="Success", id=id))
    #
    # @accepts(schema=WidgetSchema, api=api)
    # @responds(schema=WidgetSchema)
    # def put(self, widgetId: int) -> Widget:
    #     """Update Single Widget"""
    #
    #     changes: WidgetInterface = request.parsed_obj
    #     Widget = WidgetService.get_by_id(widgetId)
    #     return WidgetService.update(Widget, changes)
