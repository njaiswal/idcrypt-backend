import logging

BASE_ROUTE = "repos"
logger = logging.getLogger(__name__)


def register_routes(api):
    from .controller import api as repos_api
    api.add_namespace(repos_api, path=f"/{BASE_ROUTE}")
