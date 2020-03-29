from flask_restplus import abort

from app import docService
from app.cognito.cognitoUser import CognitoUser
from app.docs.model import DownloadDoc, Doc


class DownloadDocAuth:
    def __init__(self, request: DownloadDoc, user: CognitoUser):
        self.downloadDocRequest: DownloadDoc = request
        self.user: CognitoUser = user

    def doChecks(self):
        """
            - Check if document exists
            - Check if user has Doc Access Role
        """
        self.__checkDocument()
        self.__checkDocAccessRole()

    def __checkDocument(self):
        doc: Doc = docService.get_by_id(self.downloadDocRequest.repoId, self.downloadDocRequest.docId)
        if doc is None:
            abort(404, message='Document not found.')

        self.doc: Doc = doc

    def __checkDocAccessRole(self):
        if self.user.sub not in self.doc.downloadableBy:
            abort(403, message='Not Authorized.')
