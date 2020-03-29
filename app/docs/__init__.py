BASE_ROUTE = "docs"


def register_routes(api):
    from .controller import api as repos_api
    api.add_namespace(repos_api, path=f"/{BASE_ROUTE}")
