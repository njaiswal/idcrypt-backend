BASE_ROUTE = "account"
PARTITION_KEY = "accountId"


def register_routes(api):
    from .controller import api as account_api
    api.add_namespace(account_api, path=f"/{BASE_ROUTE}")
