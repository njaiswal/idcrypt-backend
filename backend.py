import json
import logging
import os

import awsgi
import app as idcrypt_app
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

VERSION = "v1.0"
env = os.getenv('ENV', 'test')
app = idcrypt_app.create_app(env=env)

logging.getLogger(__name__).level = logging.DEBUG
logger = logging.getLogger(__name__)

logger.debug("Application started.")


def handler(event, context):
    logger.debug('request: {}'.format(json.dumps(event, indent=4, sort_keys=True)))
    return awsgi.response(app, event, context, base64_content_types={"image/png"})
