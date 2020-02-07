from flask import request
from flask_accepts import accepts, responds
from flask_restplus import Namespace, Resource

from .service import UserService
from .schema import UserSchema
from .model import User

api = Namespace(
    name='user',
    description='User related routes',
)


@api.route("/")
class UserResource(Resource):
    """User"""

    @accepts(schema=UserSchema, api=api)
    @responds(schema=UserSchema)
    def post(self):
        """Create a Single User"""

        return UserService.create(request.parsed_obj)


@api.route("/<string:user_id>")
@api.param("user_id", "User ID")
class UserIdResource(Resource):
    @responds(schema=UserSchema)
    def get(self, user_id: str) -> User:
        """Get Single User"""

        return UserService.get_by_id(user_id)

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
