import json

from flask_restplus import abort
import logging
import pprint


from app.cognito.cognitoUser import CognitoUser

logger = logging.getLogger(__name__)


def get_cognito_user(flask_request):
    # serverless_wsgi puts following in wsgi environment dict
    # "API_GATEWAY_AUTHORIZER": event[u"requestContext"].get(u"authorizer"),
    # Refer: https://github.com/logandk/serverless-wsgi/blob/master/serverless_wsgi.py#L159

    if 'API_GATEWAY_AUTHORIZER' not in flask_request.environ:
        abort(message='Authentication error: XA')

    authorizer = flask_request.environ['API_GATEWAY_AUTHORIZER']

    if 'claims' not in authorizer:
        abort(message='Authentication error: XC')
    claims = authorizer['claims']

    if 'cognito:username' not in claims:
        abort(message='Authentication error: XU')
    username = claims['cognito:username']

    if 'email' not in claims:
        abort(message='Authentication error: XE')
    email = claims['email']

    if 'email_verified' not in claims or not claims['email_verified']:
        abort(message='Authentication error: XV')

    if 'sub' not in claims:
        abort(message='Authentication error: XS')
    sub = claims['sub']

    cognito_user = CognitoUser(username, email, sub)
    logger.info('CognitoUser - username: {}, email: {}, sub={}'.format(cognito_user.username, cognito_user.email,
                                                                       cognito_user.sub))
    return cognito_user
