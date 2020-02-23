import uuid
from datetime import datetime


class SameDomainAccount:

    def __init__(self, accountId, name, domain, email, status, createdAt):
        self.accountId = accountId
        self.name = name
        self.domain = domain
        self.email = email
        self.status = status
        self.createdAt = createdAt


class Account:
    """An Account"""

    def __init__(self, name, email, status, tier, address=None, owner=None, accountId=None, createdAt=None,
                 domain=None):
        self.accountId = uuid.uuid4() if accountId is None else accountId
        self.name = name
        self.domain = email.split('@')[1] if domain is None else domain
        self.owner = owner
        self.address = address
        self.email = email
        self.status = status
        self.tier = tier
        self.createdAt = datetime.now() if createdAt is None else createdAt
        self.members = []


class NewAccount(object):
    """New Account"""

    def __init__(self, name):
        self.name = name
