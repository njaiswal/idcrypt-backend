import json
import logging
import os

from flask import request

import app as idcrypt_app
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '%(asctime)s,%(msecs)d %(levelname)-8s [%(name)s:%(funcName)s:%(lineno)d] %(message)s',
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

    logger.info('Request API_GATEWAY_AUTHORIZER:'.ljust(35) + json.dumps(request.environ['API_GATEWAY_AUTHORIZER'], default=str))
    logger.info('Request Url:'.ljust(35) + '{}: {}'.format(request.method, request.url))
    logger.info('Request Headers:'.ljust(35) + " # ".join(headers_to_log))
    logger.info('Request Body:'.ljust(35) + str(request.get_data()))


@app.after_request
def after(response):
    headers_to_log = []
    for k, v in response.headers.items():
        headers_to_log.append('{}={}'.format(k, v))

    try:
        logger.info('Response Status:'.ljust(25) + response.status)
        logger.info('Response Headers:'.ljust(25) + " # ".join(headers_to_log))

        responseBody = json.loads(response.get_data())
        if 'base64Content' in responseBody:
            responseBody['base64Content'] = '***redacted***'

        logger.info('Response Body:'.ljust(25) + str(json.dumps(responseBody, default=str)))
    except Exception as e:
        logger.error('Could not log response due to exception: {}'.format(e))
    return response
