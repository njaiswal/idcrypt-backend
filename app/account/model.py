import uuid
from datetime import datetime


class Account:  # type: ignore
    """An Account"""

    def __init__(self, name, address, email, status, tier):
        self.accountId = uuid.uuid4()
        self.name = name
        self.address = address
        self.email = email
        self.status = status
        self.tier = tier
        self.createdAt = datetime.now()

    def with_account_id(self, accountId):
        self.accountId = accountId
        return self
