import hashlib
import json
import logging
import pprint
import time
from behave import given, when, then, step
from boto3.dynamodb.conditions import Key
from deepdiff import DeepDiff
from flask import Response
from hamcrest import *
from app import db, s3, requestService, accountService
from app.database.db import assert_dynamodb_response

base_url = '/api/v1.0'

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


@given(u'backend app is setup')
def flask_setup(context):
    assert context.client


@step(u'i am logged in as {user}')
def login(context, user):
    context.auth_header = get_fake_auth_headers(user)


@step(u'i OPTIONS "{uri}"')
def options(context, uri):
    url = '{}{}'.format(base_url, uri)

    response = context.client.options(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header})
    assert response
    context.response = response


@step(u'i GET "{uri}"')
def get(context, uri):
    url = '{}{}'.format(base_url, uri)

    response = context.client.get(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header})
    assert response
    context.response = response


@step(u"i submit create repo request with '{payload}'")
def submit_create_repo(context, payload):
    context.text = payload
    create_new_repo(context)


@step(u'i create a new repo with payload')
def create_new_repo(context):
    url = '{}{}'.format(base_url, '/repos/')
    payload: dict = json.loads(context.text)

    response = context.client.post(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header}, json=payload)
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response


@step(u"i submit create account request with '{payload}'")
def submit_create_account(context, payload):
    context.text = payload
    create_new_account(context)


@step(u'i create a new account with payload')
def create_new_account(context):
    url = '{}{}'.format(base_url, '/account/')
    payload: dict = json.loads(context.text)

    response = context.client.post(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header}, json=payload)
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response


@step(u"i update account '{accountName}' with query parameter {queryParam}")
def update_account_with_queryParam(context, accountName, queryParam):
    accountId = get_account_by_name(accountName)['accountId']

    url = '{}{}/{}?{}'.format(base_url, '/account', accountId, queryParam)

    response = context.client.put(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header})
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response


@step('i get account membership for account name \'{accountName}\'')
def membership_request(context, accountName):
    accountId = get_account_by_name(accountName)['accountId']
    get(context, '/account/{}/members'.format(accountId))


@step('i submit request of type {action} for \'{accountName}\'')
def app_request(context, action, accountName):
    assert_that(action, is_in(['joinAccount', 'leaveAccount', 'makeMeGod']))
    accountId = get_account_by_name(accountName)['accountId']
    app_request_params(context, action, accountId, accountId)


@step('i submit request of type {action} for account \'{accountName}\' and repo \'{repoName}\'')
def repo_request(context, action, accountName, repoName):
    assert_that(action, is_in(['joinAsRepoApprover', 'leaveAsRepoApprover',
                               'grantRepoAccess', 'removeRepoAccess',
                               'makeMeGod']))
    accountId = get_account_by_name(accountName)['accountId']
    repoId = get_repo_by_name(accountId, repoName)['repoId']
    app_request_params(context, action, accountId, repoId)


@step(
    u"i submit request on behalf of '{requestee}' of type {requestType} for accountName '{accountName}' and repoName '{repoName}'")
def onBehalfOf_repo_request(context, requestee, requestType, accountName, repoName):
    assert_that(requestType, is_in(['joinAsRepoApprover', 'leaveAsRepoApprover',
                                    'grantRepoAccess', 'removeRepoAccess',
                                    'makeMeGod']))
    accountId = get_account_by_name(accountName)['accountId']
    repoId = get_repo_by_name(accountId, repoName)['repoId']
    app_request_params_with_requestee(context, requestType, accountId, repoId, requesteeEmail=requestee)


@step(
    'i submit request of requestType: \'{requestType}\', accountId: \'{accountId}\', requestedOnResource: \'{requestedOnResource}\'')
def app_request_params(context, requestType, accountId, requestedOnResource):
    app_request_params_with_requestee(context, requestType, accountId, requestedOnResource)


def app_request_params_with_requestee(context, requestType, accountId, requestedOnResource, requesteeEmail=None):
    url = '{}{}'.format(base_url, '/requests/')

    effective_account_id = accountId
    if accountId == 'last_created_accountId':
        last_json_response = json.dumps(context.response.get_json())
        effective_account_id = json.loads(last_json_response)['accountId']

    payload = dict(accountId=effective_account_id,
                   requestType=requestType,
                   requestedOnResource=requestedOnResource)

    if requesteeEmail is not None:
        payload['requesteeEmail'] = requesteeEmail

    logger.info('Url: {} , Payload: {} '.format(url, payload))
    response = context.client.post(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header}, json=payload)
    assert response
    context.response = response
    context.last_submitted_request_response = response


@step(u'i try to mark accountId={accountId} and requestId={requestId} as {new_status}')
def action_request_primaryKey(context, accountId, requestId, new_status):
    effective_account_id = accountId
    if accountId == 'last_created_accountId':
        last_json_response = json.dumps(context.response.get_json())
        effective_account_id = json.loads(last_json_response)['accountId']

    url = '{}/requests/?status={}'.format(base_url, new_status)
    payload = dict(accountId=effective_account_id,
                   requestId=requestId)

    response = context.client.put(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header}, json=payload)
    assert response
    context.response = response


@step(u"i wait for last_submitted request to get '{status}'")
def wait_for_request_status(context, status):
    accountId = json.loads(json.dumps(context.last_submitted_request_response.get_json()))['accountId']
    requestId = json.loads(json.dumps(context.last_submitted_request_response.get_json()))['requestId']

    appRequest = None
    for i in range(0, 50):
        appRequest = requestService.get_by_primaryKeys(accountId, requestId)
        logger.info('Request new status = {}'.format(appRequest.status))
        if appRequest.status == status:
            break
        time.sleep(0.1)

    assert appRequest.status == status


@step(u'i mark {requestType} request as {new_status}')
def action_request(context, requestType, new_status):
    if requestType != 'last_submitted':
        get(context, '/requests/')
        my_requests: list = json.loads(json.dumps(context.response.get_json()))

        assert len(my_requests) > 0

        accountId = None
        requestId = None
        for request in my_requests:
            if request['requestType'] == requestType:
                accountId = request['accountId']
                requestId = request['requestId']
                break
    else:
        accountId = json.loads(json.dumps(context.last_submitted_request_response.get_json()))['accountId']
        requestId = json.loads(json.dumps(context.last_submitted_request_response.get_json()))['requestId']

    assert accountId is not None
    assert requestId is not None

    action_request_primaryKey(context, accountId, requestId, new_status)


@step(u"i {action} account '{accountName}'")
def update_account(context, action, accountName):
    assert_that(action, is_in(['activate', 'deactivate']))
    accountId = get_account_by_name(accountName)['accountId']
    update_account_id(context, action, accountId)


@step(u"i {action} accountId '{accountId}'")
def update_account_id(context, action, accountId):
    assert_that(action, is_in(['activate', 'deactivate']))
    status = 'inactive' if action == 'deactivate' else 'active'

    url = '{}{}/{}?status={}'.format(base_url, '/account', accountId, status)
    response = context.client.put(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header})
    assert response
    context.response = response


@then(u'i should get response with status code {code:d}')
def response_status_code(context, code):
    response: Response = context.response
    assert_that(response.status_code, equal_to(code))


@then(u"i get response with '{status_code}' and '{response}'")
def verify_response_and_status_code(context, status_code, response):
    context.text = response
    response_status_code(context, int(status_code))


@then(u'i should get response with status code {code:d} and headers')
def response_status_code_and_headers(context, code):
    response: Response = context.response
    assert_that(response.status_code, equal_to(code))

    header_dict = dict()
    for header in response.headers.to_wsgi_list():
        header_dict[header[0]] = header[1]

    expected_json: dict = json.loads(context.text)
    logger.info('OPTIONS returned headers: {}'.format(json.dumps(header_dict, indent=4, sort_keys=True)))
    ddiff = DeepDiff(header_dict, expected_json, ignore_order=True, exclude_paths="root['Allow']")
    pprint.pprint(ddiff, indent=4)
    assert not ddiff


@then(u'i should get response with status code {code:d} and data')
def response_status_code(context, code):
    response: Response = context.response
    assert_that(response.status_code, equal_to(code))

    expected_json: dict = json.loads(context.text)

    if code == 200:
        response_dict = json.loads(json.dumps(response.get_json()))
        ddiff = DeepDiff(response_dict, expected_json, ignore_order=True,
                         exclude_paths=["root['createdAt']",
                                        "root['accountId']",
                                        "root['requestId']",
                                        "root['requestedOnResource']",
                                        "root['repoId']"
                                        ],
                         exclude_regex_paths=[
                             r"root\[\d+\]\['(createdAt|accountId|repoId)'\]",
                             r"root\['updateHistory'\]\[\d+\]"
                         ])
        logger.info('Diff of actual and expected response below:')
        pprint.pprint(ddiff, indent=4)
        assert not ddiff

        # For some reason DeepDiff not working on updateHistory due to its structure in response
        if 'updateHistory' in expected_json:
            for i in range(0, len(expected_json['updateHistory']) - 1):
                expected_update_history = expected_json['updateHistory'][i]
                actual_update_history = json.loads(json.dumps(response.get_json()))['updateHistory'][i]

                ddiff = DeepDiff(actual_update_history, expected_update_history, ignore_order=True,
                                 exclude_paths=["root['updatedAt']"])
                pprint.pprint(ddiff, indent=4)
                assert not ddiff
    else:
        assert not DeepDiff(response.get_json(), expected_json, ignore_order=True)


@step(u"repo meta info file '{pathToMetaInfoFile}' is available for account '{accountName}'")
def verify_s3_repo_metaInfo(context, pathToMetaInfoFile, accountName):
    s3BucketName = get_account_by_name(accountName)['bucketName']
    bucketResource = s3.s3_resource.Bucket(s3BucketName)

    objectKeysInBucket = []
    for obj in bucketResource.objects.all():
        objectKeysInBucket.append(obj.key)

    assert pathToMetaInfoFile in objectKeysInBucket


@step(u"account with name '{accountName}' is not present")
def account_not_present(context, accountName):
    assert not accountService.account_by_name_exists(accountName)


@step(u"s3 logging bucket is missing")
def delete_s3_logging_bucket(context):
    # delete all objects in logging bucket
    bucketResource = s3.s3_resource.Bucket('idcrypt-s3-access-logs')
    bucketResource.objects.all().delete()
    bucketResource.delete()

    waiter = s3.client.get_waiter('bucket_not_exists')
    waiter.wait(Bucket='idcrypt-s3-access-logs')


@step(u"s3 bucket for account '{accountName}' is available")
def verify_s3_bucket(context, accountName):
    s3BucketName = get_account_by_name(accountName)['bucketName']

    allBucketNames = []
    for buckets in s3.client.list_buckets()['Buckets']:
        allBucketNames.append(buckets['Name'])

    assert s3BucketName in allBucketNames


@step(u"s3 bucket namespace for '{bucketNameSpace}' is exhausted")
def exhaust_s3_namespace(context, bucketNameSpace):
    for suffix in range(1000, 9999):
        if suffix % 2:
            continue
        suffixedBucketName = '{}-{}'.format(bucketNameSpace, suffix)
        s3.client.create_bucket(
            Bucket=suffixedBucketName,
            CreateBucketConfiguration={
                'LocationConstraint': s3.region
            }
        )


def get_fake_auth_headers(email: str):
    sub = None
    if email == 'jrn@jrn-limited.com':
        sub = '01993b92-2900-48f0-a056-85688aaef3be'
    if email == 'rashi@jrn-limited.com':
        sub = 'af481bdf-d195-41ee-a297-1ed645624a1b'
    if email == 'nishant@jrn-limited.com':
        sub = 'e7ba07ac-caaa-4bb9-89a5-4d8c8b008421'
    if email == 'joe@jrn-limited.com':
        sub = '30accff5-916d-47d7-bdbb-a3d7dc95feec'
    if email == 'sam@jrn-limited.com':
        sub = '86c8644c-d74e-495b-afe9-7eaff234bea9'
    if email == 'kevin@jrn-limited.com':
        sub = '85ee1019-9c53-4da4-a749-b9714f301155'
    if email == 'bob@jrn-limited.com':
        sub = 'a9c71a15-60ab-4e13-9ed9-521b377ed741'

    if sub is None:
        sub = hashlib.md5(email.encode()).hexdigest()

    return {
        'claims': {
            'cognito:username': email.split('@')[0],
            'email': email,
            'email_verified': 'true',
            'sub': sub
        }
    }


def get_account_by_name(accountName, retry=False):
    table = db.dynamodb_resource.Table('Accounts-test')

    resp = table.query(
        IndexName='AccountNameIndex',
        KeyConditionExpression=Key('name').eq(accountName),
        Select='ALL_PROJECTED_ATTRIBUTES'
    )
    assert_dynamodb_response(resp, expected_attribute='Items')

    # If we do not find the account give it another try
    if resp['Count'] == 0 and not retry:
        logger.info('Did not find account with name {}. Going to retry after 1 sec'.format(accountName))
        time.sleep(1)
        return get_account_by_name(accountName, retry=True)

    assert_that(len(resp['Items']), is_not(0), reason="Get account by name failed")

    return resp['Items'][0]


def get_repo_by_name(accountId, repoName, retry=False):
    table = db.dynamodb_resource.Table('Repos-test')

    resp = table.query(
        IndexName='AccountIdAndRepoNameIndex',
        KeyConditionExpression=Key('accountId').eq(accountId) & Key('name').eq(repoName),
        Select='ALL_PROJECTED_ATTRIBUTES'
    )

    assert_dynamodb_response(resp, expected_attribute='Items')

    # If we do not find the account give it another try
    if resp['Count'] == 0 and not retry:
        logger.info('Did not find repo with name {}. Going to retry after 1 sec'.format(repoName))
        time.sleep(1)
        return get_repo_by_name(accountId, repoName, retry=True)

    assert_that(len(resp['Items']), is_not(0), reason="Get repo by name failed")

    return resp['Items'][0]
