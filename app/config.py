from typing import List, Type


class BaseConfig:
    CONFIG_NAME = "base"
    USE_MOCK_EQUIVALENCY = False
    DEBUG = False
    ERROR_404_HELP = False


class DevelopmentConfig(BaseConfig):
    CONFIG_NAME = "dev"
    SECRET_KEY = ""
    DEBUG = True
    DYNAMODB_ENDPOINT_URL = "https://dynamodb.eu-west-1.amazonaws.com"
    S3_ENDPOINT_URL = "https://s3.eu-west-1.amazonaws.com"
    IDP_ENDPOINT_URL = "https://cognito-idp.eu-west-1.amazonaws.com"
    TEXT_EXTRACT_URL = "https://textract.eu-west-1.amazonaws.com"
    ES_ENDPOINT_URL = "https://search-idcrypt-dev-czxbeuummnivrvmdjmpfknnz5y.eu-west-1.es.amazonaws.com"
    REGION_NAME = "eu-west-1"
    COGNITO_USERPOOL_ID = 'eu-west-1_R8z2Oswjr'
    LOGGING_BUCKET_NAME = 'idcrypt-s3-access-logs'
    UPLOAD_ERRORS_BUCKET = 'idcrypt-upload-errors-dev'


class TestingConfig(BaseConfig):
    CONFIG_NAME = "test"
    DEBUG = True
    TESTING = True
    DYNAMODB_ENDPOINT_URL = "http://localhost:8000"
    S3_ENDPOINT_URL = "http://localhost:4500"
    IDP_ENDPOINT_URL = "https://cognito-idp.eu-west-1.amazonaws.com"
    TEXT_EXTRACT_URL = "https://textract.eu-west-1.amazonaws.com"
    ES_ENDPOINT_URL = "http://localhost:9200"
    REGION_NAME = "eu-west-1"
    COGNITO_REGION = 'eu-west-1'
    COGNITO_USERPOOL_ID = 'eu-west-1_R8z2Oswjr'
    LOGGING_BUCKET_NAME = 'idcrypt-s3-access-logs'
    # optional
    COGNITO_APP_CLIENT_ID = '6bk8pp1tf9cla2rq6n9q0c9uop'  # client ID you wish to verify user is authenticated against
    UPLOAD_ERRORS_BUCKET = 'idcrypt-upload-errors-test'


EXPORT_CONFIGS: List[Type[BaseConfig]] = [
    DevelopmentConfig,
    TestingConfig,
]
config_by_name = {cfg.CONFIG_NAME: cfg for cfg in EXPORT_CONFIGS}
