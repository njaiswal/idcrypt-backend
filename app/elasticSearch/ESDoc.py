from datetime import datetime
from elasticsearch_dsl import Document, Date, Completion, Keyword, Text, Integer


class ESDoc(Document):
    # unique IDs can only be used to filter search results
    repoId = Keyword()
    docId = Keyword()
    accountId = Keyword()
    uploadedBy = Keyword()

    # Names these also are keywords and only can be used to filter search results
    repoName = Keyword()
    accountName = Keyword()
    status = Keyword()

    # These will provide auto complete suggestions
    uploadedByEmail = Completion()
    docType = Completion()

    # Full text search. This needs proper analyzer and stop words.
    text = Text()
    name = Text()

    # Age related
    createdAt = Date()      # Date when dynamodb doc was created.
    retention = Integer()
    ingestedAt = Date()     # Date when elastic search ingested this doc

    # Misc
    errorMessage = Text()

    # Arrays
    downloadableBy = Keyword()

    def save(self, **kwargs):
        self.ingestedAt = datetime.now()
        return super().save(**kwargs)
