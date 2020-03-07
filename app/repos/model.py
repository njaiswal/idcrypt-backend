import uuid
from datetime import datetime
from typing import List


class NewRepo(object):
    """New Repo"""

    def __init__(self, name, desc, retention):
        self.name = name
        self.desc = desc
        self.retention = retention


class Repo(object):
    """Repo"""

    def __init__(self,
                 accountId,
                 name,
                 desc,
                 retention,
                 approvers: List[str],
                 users: List[str],
                 repoId=None,
                 createdAt=None):
        self.repoId = str(uuid.uuid4()) if repoId is None else repoId
        self.accountId = accountId
        self.name = name
        self.desc = desc
        self.retention = retention
        self.approvers = approvers
        self.users = users
        self.createdAt = datetime.now() if createdAt is None else createdAt
