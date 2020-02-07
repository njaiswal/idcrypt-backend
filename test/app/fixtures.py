import logging
import pytest
from app import create_app

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def app():
    return create_app(env="test")


@pytest.fixture
def client(app):
    return app.test_client()
