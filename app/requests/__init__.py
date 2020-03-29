BASE_ROUTE = "requests"


def register_routes(api):
    from .controller import api as requests_api
    api.add_namespace(requests_api, path=f"/{BASE_ROUTE}")
