BASE_ROUTE = "accounts"


def register_routes(api):
    from .controller import api as accounts_api
    api.add_namespace(accounts_api, path=f"/{BASE_ROUTE}")
