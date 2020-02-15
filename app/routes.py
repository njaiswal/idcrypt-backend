def register_routes(api):
    from app.account import register_routes as attach_account_route
    from app.accounts import register_routes as attach_accounts_route

    # Add routes
    attach_account_route(api)
    attach_accounts_route(api)
