import pytest
from deepdiff import DeepDiff
from flask import Response
from flask.testing import FlaskClient
from test.app.fixtures import client, app  # noqa
from app.user import BASE_ROUTE
import logging
from random_words import RandomWords, LoremIpsum, RandomEmails, RandomNicknames
from backend import VERSION

logger = logging.getLogger(__name__)
rand = RandomWords()
rand_mails = RandomEmails()
rand_names = RandomNicknames()


def create_payload():
    return dict(
        firstName=rand_names.random_nick(gender='m'),
        lastName=rand_names.random_nick(gender='m'),
        status="active",
        email=rand_mails.randomMail(),
    )


class TestUserResource:
    def test_post(self, client: FlaskClient):
        payload = create_payload()
        result = client.post(f"/api/{VERSION}/{BASE_ROUTE}/", json=payload).get_json()
        logger.info('result: %s', result)
        assert not DeepDiff(payload, result, ignore_order=True,
                            exclude_paths=["root['createdAt']", "root['accountId']", "root['userId']"])

    def test_post_missing_required(self, client: FlaskClient):  # noqa
        payload = create_payload()
        # Remove a required field from payload
        payload.pop("firstName")

        response: Response = client.post(f"/api/{VERSION}/{BASE_ROUTE}/", json=payload)
        logger.info('response status code: {}, json: {}'.format(response.status_code, response.get_json()))

        assert response.status_code == 400
        assert response.get_json() == {'schema_errors': {'firstName': ['Missing data for required field.']}}

    def test_post_incorrect_type(self, client: FlaskClient):  # noqa
        payload = create_payload()
        # Remove a name from payload and add name as int instead
        payload.pop("firstName")
        payload['firstName'] = 123456

        response: Response = client.post(f"/api/{VERSION}/{BASE_ROUTE}/", json=payload)
        logger.info('response status code: {}, json: {}'.format(response.status_code, response.get_json()))

        assert response.status_code == 400
        assert response.get_json() == {'schema_errors': {'firstName': ['Not a valid string.']}}

    def test_get(self, client: FlaskClient):  # noqa
        payload = create_payload()
        create_response = client.post(f"/api/{VERSION}/{BASE_ROUTE}/", json=payload).get_json()

        get_response = client.get(f"/api/{VERSION}/{BASE_ROUTE}/{create_response['userId']}").get_json()
        logger.info(f"get_response = {get_response}")
        assert not DeepDiff(create_response, get_response, ignore_order=True)

    def test_get_not_found(self, client: FlaskClient):  # noqa
        response: Response = client.get(f"/api/{VERSION}/{BASE_ROUTE}/{rand.random_word()}")
        logger.info('response status code: {}, json: {}'.format(response.status_code, response.get_json()))
        assert response.status_code == 404
        assert str(response.get_json()['message']).startswith('User ID not found')
