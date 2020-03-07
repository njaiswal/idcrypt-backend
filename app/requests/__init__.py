import logging

BASE_ROUTE = "requests"
logger = logging.getLogger(__name__)


def register_routes(api):
    from .controller import api as requests_api
    api.add_namespace(requests_api, path=f"/{BASE_ROUTE}")
