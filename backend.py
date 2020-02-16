import json
import logging
import os

# import awsgi
from flask import request

import app as idcrypt_app
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(lineno)d] %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

VERSION = "v1.0"
env = os.getenv('ENV', 'test')
app = idcrypt_app.create_app(env=env)

logger = logging.getLogger(__name__)
logger.debug("Application started in {} env".format(env))


@app.before_request
def log_request_info():
    headers_to_log = []
    for k, v in request.headers.items():
        if k != 'Authorization':
            headers_to_log.append('{}={}'.format(k, v))
        else:
            headers_to_log.append('{}=***redacted***'.format(k))

    logger.debug('Request REMOTE_USER:'.ljust(25) + json.dumps(request.environ['REMOTE_USER']))
    logger.debug('Request Url:'.ljust(25) + '{}: {}'.format(request.method, request.url))
    logger.debug('Request Headers:'.ljust(25) + " # ".join(headers_to_log))
    logger.debug('Request Body:'.ljust(25) + str(request.get_data()))


@app.after_request
def after(response):
    headers_to_log = []
    for k, v in response.headers.items():
        headers_to_log.append('{}={}'.format(k, v))

    try:
        logger.debug('Response Status:'.ljust(25) + response.status)
        logger.debug('Response Headers:'.ljust(25) + " # ".join(headers_to_log))
        logger.debug('Response Body:'.ljust(25) + str(response.get_data()))
    except:
        logger.error('Could not log response due to exception')
    return response

# def handler(event, context):
#     logger.debug('request: {}'.format(json.dumps(event, indent=4, sort_keys=True)))
#     response = awsgi.response(app, event, context, base64_content_types={"image/png"})
#     logger.debug(json.dumps(response, indent=4, sort_keys=4))
#     return response
