def register_routes(api):
    from app.account import register_routes as attach_account_route
    from app.accounts import register_routes as attach_accounts_route
    from app.requests import register_routes as attach_requests_route

    # Add routes
    attach_account_route(api)
    attach_accounts_route(api)
    attach_requests_route(api)
