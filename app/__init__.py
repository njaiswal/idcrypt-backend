from flask import Flask
from flask_restplus import Api, abort
from webargs.flaskparser import parser
from app.database.db import DB
from flask_cors import CORS

db = DB()


def create_app(version="v1.0", env=None):
    from app.routes import register_routes
    from app.config import config_by_name

    app = Flask(__name__)

    # In test and dev allow cors from localhost
    cors_origins = [r'^https://(dev|qa|uat).idcrypt.io', 'https://idcrypt.io']
    if env == 'test' or env == 'dev':
        cors_origins.append('http://localhost:4200')

    CORS(app, resource={r'/api/*'}, origins=cors_origins, supports_credentials=True)

    api = Api(
        app,
        title='IDCrypt Admin API',
        version=version,
        description='IDCrypt Administration API',
        doc='/api/{}'.format(version),
        prefix='/api/{}'.format(version)
    )

    app.config.from_object(config_by_name[env or "test"])

    # Initialize DB
    db.init(app)

    # Register routes
    register_routes(api)

    return app


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(error, req, schema, status_code, headers):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    abort(422, errors=error.messages)
