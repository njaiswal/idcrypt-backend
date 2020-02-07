def create_tables(env=None):
    from app.account import create_table as create_account_table
    from app.user import create_table as create_user_table

    # Add tables
    create_account_table(env=env)
    create_user_table(env=env)
