def register_routes(api):
    from app.account import register_routes as attach_account_route
    from app.user import register_routes as attach_user_route

    # Add routes
    attach_account_route(api)
    attach_user_route(api)
