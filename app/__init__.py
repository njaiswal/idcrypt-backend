import resource
from botocore.client import BaseClient
from flask import Flask, jsonify, Blueprint
from flask_restplus import Api
import boto3
import logging
from app.database.db import DB
from flask_cors import CORS

logger = logging.getLogger(__name__)
db = DB()


def create_app(version="v1.0", env=None):
    from app.routes import register_routes
    from app.config import config_by_name
    from app.db_schema import create_tables

    app = Flask(__name__)
    CORS(app, resource={r"/*": {"origins": "*"}})   # Todo: take this as configuration. in prod restrict to *.idcrypt.io

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

    @app.route("/health")
    def health():
        return jsonify("healthy")

    return app
