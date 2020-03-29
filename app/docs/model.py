import uuid
from datetime import datetime
from enum import Enum
from typing import List


class DocImage(object):
    def __init__(self, name=None, base64Content=None, contentType=None):
        self.name = name
        self.base64Content = base64Content
        self.contentType = contentType


class DocPrimaryKeys(object):
    def __init__(self, accountId, repoId):
        self.repoId = repoId
        self.accountId = accountId


class DownloadDoc(DocPrimaryKeys):
    def __init__(self, accountId, repoId, docId):
        super().__init__(accountId, repoId)
        self.docId = docId


class SearchDoc(DocPrimaryKeys):
    """Search Doc"""

    def __init__(self, accountId, repoId, text=None, downloadable=None):
        super().__init__(accountId, repoId)
        self.repoId = repoId
        self.accountId = accountId
        self.text = text
        self.downloadable = downloadable


class NewDoc(DocPrimaryKeys):
    """New Doc"""

    def __init__(self, accountId, repoId, name):
        super().__init__(accountId, repoId)
        self.name = name


class DocStatus(Enum):
    initialized = 'initialized'
    beingProcessed = 'beingProcessed'
    expired = 'expired'
    failed = 'failed'
    successfullyProcessed = 'successfullyProcessed'
    indexed = 'indexed'


class DocType(Enum):
    passport = 'passport'
    nationalIdCard = 'nationalIdCard'
    drivingLicence = 'drivingLicence'
    bankStatement = 'bankStatement'
    utilityBill = 'utilityBill'
    other = 'other'

    @classmethod
    def from_str(cls, label):
        if label == 'passport':
            return cls.passport
        elif label == 'nationalIdCard':
            return cls.nationalIdCard
        elif label == 'drivingLicence':
            return cls.drivingLicence
        elif label == 'bankStatement':
            return cls.bankStatement
        elif label == 'utilityBill':
            return cls.utilityBill
        elif label == 'other':
            return cls.other
        else:
            return None


class Doc(object):
    """Doc"""

    def __init__(self,
                 repoId: str,
                 accountId: str,
                 retention: int,
                 status: DocStatus,
                 uploadedBy: str,
                 downloadableBy: List[str],
                 downloadable: bool = None,
                 docType: DocType = None,
                 text: str = None,
                 name: str = None,
                 docId: str = None,
                 createdAt=None,
                 errorMessage: str = None,
                 uploadedByEmail: str = None):
        self.docId = str(uuid.uuid4()) if docId is None else docId
        self.repoId: str = repoId
        self.accountId: str = accountId
        self.docType: DocType = docType
        self.retention: int = retention
        self.status: DocStatus = status
        self.uploadedBy = uploadedBy
        self.downloadableBy = downloadableBy
        self.downloadable = False if downloadable is None else downloadable
        self.text: str = text
        self.name: str = name
        self.createdAt = datetime.now() if createdAt is None else createdAt
        self.errorMessage = errorMessage
        self.uploadedByEmail = uploadedByEmail
