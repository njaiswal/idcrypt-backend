import json

from flask_restplus import abort
import logging

from app.cognito.cognitoUser import CognitoUser

logger = logging.getLogger(__name__)


def get_cognito_user(flask_request):
    # serverless_wsgi puts following in wsgi environment dict
    # "REMOTE_USER": event[u"requestContext"]
    # Refer: https://github.com/logandk/serverless-wsgi/blob/master/serverless_wsgi.py#L134

    if 'REMOTE_USER' not in flask_request.environ:
        abort(message='Authentication error: XR')

    requestContext = json.loads(flask_request.environ['REMOTE_USER'])

    if 'authorizer' not in requestContext:
        abort(message='Authentication error: XA')
    authorizer = requestContext['authorizer']

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
