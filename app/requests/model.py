import uuid
from datetime import datetime


class AppRequest:
    """ App Request """

    def __init__(self,
                 accountId,
                 accountName,
                 requestType,
                 requestedOnResource,
                 requestedOnResourceName,
                 requestee,
                 requestor,
                 requesteeEmail,
                 requestorEmail,
                 requestId=None,
                 status=None,
                 createdAt=None,
                 updateHistory=None):
        self.requestId = uuid.uuid4() if requestId is None else requestId
        self.accountId = accountId
        self.accountName = accountName
        self.requestee = requestee
        self.requestor = requestor
        self.requesteeEmail = requesteeEmail
        self.requestorEmail = requestorEmail
        self.requestType = requestType
        self.requestedOnResource = requestedOnResource
        self.requestedOnResourceName = requestedOnResourceName
        self.status = status if status is not None else 'pending'
        self.createdAt = datetime.now() if createdAt is None else createdAt
        self.updateHistory = updateHistory if updateHistory is not None else []


class NewAppRequest:
    """ New App Request """

    def __init__(self, accountId, requestType, requestedOnResource, requestee=None):
        self.accountId = accountId
        self.requestType = requestType
        self.requestedOnResource = requestedOnResource
        self.requestee = requestee


class UpdateAppRequest:
    """Update App Request """

    def __init__(self, accountId, requestId):
        self.accountId = accountId
        self.requestId = requestId


class UpdateHistory:
    """Update History of Request """

    def __init__(self, action, updatedBy, updatedByEmail, updatedAt):
        self.action = action
        self.updatedBy = updatedBy
        self.updatedByEmail = updatedByEmail
        self.updatedAt = updatedAt
