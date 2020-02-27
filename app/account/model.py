import uuid
from datetime import datetime
from typing import List

from app.repos.model import NewRepo


class SameDomainAccount:

    def __init__(self, accountId, name, domain, email, status, createdAt, owner, members: List[str], admins: List[str]):
        self.accountId = accountId
        self.name = name
        self.domain = domain
        self.email = email
        self.status = status
        self.createdAt = createdAt
        self.owner = owner
        self.members: List[str] = members
        self.admins: List[str] = admins


class Account:
    """An Account"""

    def __init__(self, name, email, status, tier, members, admins, owner, address=None, accountId=None, createdAt=None,
                 domain=None, bucketName=None):
        self.accountId = uuid.uuid4() if accountId is None else accountId
        self.name = name
        self.domain = email.split('@')[1] if domain is None else domain
        self.owner = owner
        self.address = address
        self.email = email
        self.status = status
        self.tier = tier
        self.createdAt = datetime.now() if createdAt is None else createdAt
        self.members: List[str] = members
        self.admins: List[str] = admins
        self.bucketName = bucketName


class NewAccount(object):
    """New Account"""

    def __init__(self, name, repo: NewRepo):
        self.name = name
        self.repo: NewRepo = repo
