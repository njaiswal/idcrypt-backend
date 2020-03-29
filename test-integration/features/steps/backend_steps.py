import hashlib
import json
import logging
import os
import pprint
import time
import uuid

from behave import given, when, then, step
from boto3.dynamodb.conditions import Key
from deepdiff import DeepDiff
from flask import Response
from hamcrest import *
from app import db, s3, requestService, accountService, docService
from app.database.db import assert_dynamodb_response
from app.docs.model import Doc

base_url = '/api/v1.0'

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')
uploadBucketName = 'idcrypt-document-uploads-test'
uploadErrorsBucketName = 'idcrypt-upload-errors-test'


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


@step(u"i try to download doc with accountId: '{accountId}' repoId: '{repoId}' docId: '{docId}'")
def download_doc(context, accountId, repoId, docId):
    effective_accountId = accountId
    effective_repoId = repoId
    effective_docId = docId

    last_json_response = json.loads(json.dumps(context.response.get_json()))
    if isinstance(last_json_response, list):
        last_json_response = last_json_response[0]

    if accountId == 'last_saved_accountId':
        assert 'accountId' in last_json_response
        effective_accountId = last_json_response['accountId']

    if repoId == 'last_saved_repoId':
        assert 'repoId' in last_json_response
        effective_repoId = last_json_response['repoId']

    if docId == 'last_saved_docId':
        assert 'docId' in last_json_response
        effective_docId = last_json_response['docId']

    get(context,
        '/docs/download?accountId={}&repoId={}&docId={}'.format(effective_accountId, effective_repoId, effective_docId))

@step(u'i GET "{uri}"')
def get(context, uri):
    url = '{}{}'.format(base_url, uri)

    response = context.client.get(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header})
    assert response
    context.response = response


@step(u"last_uploaded_file appears in upload errors bucket")
def stat_last_uploaded_file_in_errors_bucket(context):
    uploadErrorsBucket = s3.resource.Bucket(uploadErrorsBucketName)
    assert context.last_uploaded_file is not None

    fileFound = False
    for i in range(0, 30):
        objectKeys = dict()
        for s3Object in uploadErrorsBucket.objects.all():
            objectKeys[s3Object.key] = True

        logger.info('Objects in upload Bucket: {}'.format(objectKeys))
        if context.last_uploaded_file not in objectKeys:
            time.sleep(0.5)
            continue
        else:
            fileFound = True
            break
    assert fileFound


@step(u"last_uploaded_file is removed from upload bucket")
def stat_last_uploaded_file(context):
    uploadBucket = s3.resource.Bucket(uploadBucketName)
    assert context.last_uploaded_file is not None

    fileFound = True
    for i in range(0, 30):
        objectKeys = dict()
        for s3Object in uploadBucket.objects.all():
            objectKeys[s3Object.key] = True

        logger.info('Objects in upload Bucket: {}'.format(objectKeys))
        if context.last_uploaded_file in objectKeys:
            time.sleep(0.5)
            continue
        else:
            fileFound = False
            break
    assert not fileFound


@step(u"i upload {fileName} with '{repoId}' and '{docId}' and type '{docType}'")
def upload_doc(context, fileName, repoId, docId, docType):
    last_json_response = json.loads(json.dumps(context.response.get_json()))
    if repoId == 'saved_repoId':
        assert 'repoId' in last_json_response
        repoId = last_json_response['repoId']
    if docId == 'saved_docId':
        assert 'docId' in last_json_response
        docId = last_json_response['docId']

    if repoId == 'incorrect':
        repoId = str(uuid.uuid4())
        docId = str(uuid.uuid4())

    s3UploadDoc(context, fileName, repoId, docId, docType)


@step(
    u"i submit create doc request with for account with name '{accountName}' and repo with name '{repoName}' and customer name '{name}'")
def submit_create_doc(context, accountName, repoName, name):
    accountId = get_account_by_name(accountName)['accountId']
    repoId = get_repo_by_name(accountId, repoName)['repoId']

    assert accountId is not None
    assert repoId is not None

    payload = dict()
    payload['accountId'] = accountId
    payload['repoId'] = repoId
    payload['name'] = name
    submit_create_resource(context, 'doc', json.dumps(payload))


@step(u"i query downloadable docs for account name '{accountName}' and repo name '{repoName}' and '{text}'")
def query_downloadable_docs_by_account_repo_name(context, accountName, repoName, text):
    query_docs(context, accountName, repoName, text, downloadable=True)


@step(u"i query docs for account name '{accountName}' and repo name '{repoName}' and '{text}'")
def query_docs_by_account_repo_name(context, accountName, repoName, text):
    query_docs(context, accountName, repoName, text)


def query_docs(context, accountName, repoName, text, downloadable=None):
    time.sleep(2.0)
    accountId = get_account_by_name(accountName)['accountId']
    repoId = get_repo_by_name(accountId, repoName)['repoId']
    get(context, '/docs/?accountId={}&repoId={}{}{}'.format(
        accountId,
        repoId,
        '&text={}'.format(text) if text != 'null' else '',
        '&downloadable=true'.format(text) if downloadable is not None else ''
    ))


@step(u"i submit create {resource} request with '{payload}'")
def submit_create_resource(context, resource, payload):
    if 'accountId' in payload and json.loads(payload)['accountId'] == 'last_created_accountId':
        last_json_response = json.dumps(context.response.get_json())
        effective_account_id = json.loads(last_json_response)['accountId']
        payload_dict = json.loads(payload)
        payload_dict['accountId'] = effective_account_id
        payload = json.dumps(payload_dict)

    context.text = payload
    create_new_resource(context, resource)


@step(u'i create a new {resource} with payload')
def create_new_resource(context, resource):
    assert resource in ['repo', 'doc', 'account']

    uri = '{}s'.format(resource) if resource in ['repo', 'doc'] else '{}'.format(resource)
    url = '{}{}'.format(base_url, '/{}/'.format(uri))
    payload: dict = json.loads(context.text)

    response = context.client.post(url, environ_base={'API_GATEWAY_AUTHORIZER': context.auth_header}, json=payload)
    assert response

    assert response.headers.get('Access-Control-Allow-Origin') == 'http://localhost:4200'
    assert response.headers.get('Access-Control-Allow-Credentials') == 'true'
    context.response = response
    context.last_created_resource_response = response


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
    effective_requestedOnResource = requestedOnResource

    if context.response.get_json() is not None:
        last_json_response = json.loads(json.dumps(context.response.get_json()))
        if isinstance(last_json_response, list):
            last_json_response = last_json_response[0]

        if accountId == 'last_created_accountId':
            assert 'accountId' in last_json_response
            effective_account_id = last_json_response['accountId']

        if 'last_created_repoId' in requestedOnResource:
            assert 'repoId' in last_json_response
            effective_requestedOnResource = effective_requestedOnResource.replace('last_created_repoId',
                                                                                  last_json_response['repoId'])

        if 'last_created_docId' in requestedOnResource:
            assert 'docId' in last_json_response
            effective_requestedOnResource = effective_requestedOnResource.replace('last_created_docId',
                                                                                  last_json_response['docId'])

    payload = dict(accountId=effective_account_id,
                   requestType=requestType,
                   requestedOnResource=effective_requestedOnResource)

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


@step(u"text for last_created doc is populated")
def docText(context):
    repoId = json.loads(json.dumps(context.last_created_resource_response.get_json()))['repoId']
    docId = json.loads(json.dumps(context.last_created_resource_response.get_json()))['docId']
    doc: Doc = docService.get_by_id(repoId, docId)
    logger.info('Document text: {}'.format(doc.text))
    assert len(doc.text) > 10


@step(u"i wait for last_created doc to get '{status}'")
def wait_for_doc_status(context, status):
    repoId = json.loads(json.dumps(context.last_created_resource_response.get_json()))['repoId']
    docId = json.loads(json.dumps(context.last_created_resource_response.get_json()))['docId']

    doc = None
    for i in range(0, 200):
        doc: Doc = docService.get_by_id(repoId, docId)
        logger.info('Doc new status = {}'.format(doc.status))
        if doc.status == status:
            break
        time.sleep(0.1)

    assert doc.status == status


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
                                        "root['repoId']",
                                        "root['docId']",
                                        "root['base64Content']"
                                        ],
                         exclude_regex_paths=[
                             r"root\[\d+\]\['(createdAt|accountId|repoId|docId)'\]",
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
    bucketResource = s3.resource.Bucket(s3BucketName)

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
    bucketResource = s3.resource.Bucket('idcrypt-s3-access-logs')
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


def s3UploadDoc(context, fileName, repoId, docId, docType):
    assert os.path.isfile(fileName)
    key = 'private/cognito-identity-xxxxxx/{}/{}/{}'.format(repoId, docId, docType)
    s3.client.upload_file(fileName, uploadBucketName, key)
    context.last_uploaded_file = key


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
