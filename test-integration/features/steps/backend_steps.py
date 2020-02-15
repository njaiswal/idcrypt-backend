import hashlib
import json
import logging

from behave import given, when, then, step
from boto3.dynamodb.conditions import Key
from deepdiff import DeepDiff
from flask import Response
from hamcrest import *

from app import db

base_url = '/api/v1.0'

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


@given(u'backend app is setup')
def flask_setup(context):
    assert context.client


@step(u'i am logged in as {user}')
def get(context, user):
    context.auth_header = get_fake_auth_headers(user)


@when(u'i GET "{uri}"')
def get(context, uri):
    url = '{}{}'.format(base_url, uri)
    headers = {'requestContext': context.auth_header}
    log_request_info(url=url, headers=headers, body=None)

    response = context.client.get(url, headers=headers)
    log_response_info(response)
    assert response
    context.response = response


@when(u'i create a new account without a name')
def create_new_account_without_name(context):
    create_new_account(context, None)


@step(u'i create a new account with name {accountName}')
def create_new_account(context, accountName):
    url = '{}{}'.format(base_url, '/account/')
    headers = {'requestContext': context.auth_header}
    payload = dict(name=accountName)
    log_request_info(url=url, headers=headers, body=payload)

    response = context.client.post(url, headers=headers, json=payload)
    log_response_info(response)
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response


@step(u"i update account '{accountName}' with query parameter {queryParam}")
def update_account_with_queryParam(context, accountName, queryParam):
    accountId = get_account_id_by_name(accountName)

    url = '{}{}/{}?{}'.format(base_url, '/account', accountId, queryParam)
    headers = {'requestContext': context.auth_header}
    log_request_info(url=url, headers=headers)

    response = context.client.put(url, headers=headers)
    log_response_info(response)
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response


@step(u"i {action} account '{accountName}'")
def update_account(context, action, accountName):
    assert_that(action, is_in(['activate', 'deactivate']))
    accountId = get_account_id_by_name(accountName)
    update_account_id(context, action, accountId)


@step(u"i {action} accountId '{accountId}'")
def update_account_id(context, action, accountId):
    assert_that(action, is_in(['activate', 'deactivate']))
    status = 'inactive' if action == 'deactivate' else 'active'

    url = '{}{}/{}?status={}'.format(base_url, '/account', accountId, status)
    headers = {'requestContext': context.auth_header}
    log_request_info(url=url, headers=headers)

    response = context.client.put(url, headers=headers)
    log_response_info(response)
    assert response
    context.response = response


@then(u'i should get response with status code {code:d} and data')
def response_status_code(context, code):
    response: Response = context.response
    assert_that(response.status_code, equal_to(code))

    expected_json = json.loads(context.text)

    if code == 200:
        assert not DeepDiff(response.get_json(), expected_json, ignore_order=True,
                            exclude_paths=["root['createdAt']", "root['accountId']"],
                            exclude_regex_paths={r"root\[\d+\]\['(createdAt|accountId)'\]"})
    else:
        assert not DeepDiff(response.get_json(), expected_json, ignore_order=True)


def get_fake_auth_headers(email: str):
    return json.dumps(
        {
            'authorizer': {
                'claims': {
                    'cognito:username': email.split('@')[0],
                    'email': email,
                    'email_verified': 'true',
                    'sub': hashlib.md5(email.encode()).hexdigest()
                }
            }
        })


def get_account_id_by_name(accountName):
    table = db.dynamodb_resource.Table('Accounts-test')

    resp = table.query(
        IndexName='AccountNameIndex',
        KeyConditionExpression=Key('name').eq(accountName),
        Select='ALL_PROJECTED_ATTRIBUTES'
    )
    assert_that(len(resp['Items']), is_not(0))

    return resp['Items'][0]['accountId']


# When running tests following methods from flask app are not invoked. Hence copying them over here.
def log_request_info(url=None, headers=None, body=None):
    headers_to_log = []
    for k, v in headers.items():
        if k != 'Authorization':
            headers_to_log.append('{}={}'.format(k, v))
        else:
            headers_to_log.append('{}=***redacted***'.format(k))

    logger.debug('Request Url:'.ljust(25) + url)
    logger.debug('Request Headers:'.ljust(25) + " # ".join(headers_to_log))
    logger.debug('Request Body:'.ljust(25) + str(body))


def log_response_info(response):
    headers_to_log = []
    for k, v in response.headers.items():
        headers_to_log.append('{}={}'.format(k, v))

    logger.debug('Response Status:'.ljust(25) + response.status)
    logger.debug('Response Headers:'.ljust(25) + " # ".join(headers_to_log))
    logger.debug('Response Body:'.ljust(25) + str(response.get_data()))
    return response
