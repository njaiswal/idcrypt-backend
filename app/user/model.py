import uuid
from datetime import datetime


class User:  # type: ignore
    """A User"""

    def __init__(self, firstName, lastName, email, status):
        self.userId = uuid.uuid4()
        self.accountId = 'No_Account_Association_Yet'  # This can be very bad if someone creates account with same name
        self.firstName = firstName
        self.lastName = lastName
        self.email = email
        self.status = status
        self.createdAt = datetime.now()

    def with_account_id(self, accountId):
        self.accountId = accountId
        return self
