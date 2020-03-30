from flask import Flask
from flask_restplus import Api, abort
from webargs.flaskparser import parser
from app.cognito.idp import IDP
from app.database.db import DB
from flask_cors import CORS

from app.docs.service import DocService
from app.elasticSearch.es import ES
from app.repos.service import RepoService
from app.requests.service import RequestService
from app.account.service import AccountService
from app.accounts.service import AccountsService
from app.storage.s3 import S3

db = DB()
s3 = S3()
idp = IDP()
accountService: AccountService = AccountService()
accountsService: AccountsService = AccountsService()
requestService: RequestService = RequestService()
repoService: RepoService = RepoService()
docService: DocService = DocService()
es = ES()


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

    # Initialize IDP for Admin queries
    idp.init(app.config.get('REGION_NAME'), app.config.get('IDP_ENDPOINT_URL'), app.config.get('COGNITO_USERPOOL_ID'))

    # Initialize DB
    db.init(app.config.get('REGION_NAME'), app.config.get('DYNAMODB_ENDPOINT_URL'))

    # Initialize S3
    s3.init(app.config.get('REGION_NAME'), app.config.get('S3_ENDPOINT_URL'), app.config.get('LOGGING_BUCKET_NAME'))

    # Initialize services
    accountService.init(db, 'Accounts-{}'.format(env))
    accountsService.init(db, 'Accounts-{}'.format(env))
    requestService.init(db, 'Requests-{}'.format(env))
    repoService.init(db, 'Repos-{}'.format(env))
    docService.init(db, 'Docs-{}'.format(env))

    # Initialize ES client
    es.init(app.config.get('REGION_NAME'), app.config.get('ES_ENDPOINT_URL'), accountService, repoService, idp)

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
