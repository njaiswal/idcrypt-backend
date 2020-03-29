from app.requests.model import RequestType


def getResourceType(requestType: str) -> str:
    if requestType in [
        RequestType.joinAccount.value, RequestType.leaveAccount.value
    ]:
        return 'account'

    if requestType in [
        RequestType.joinAsRepoApprover.value, RequestType.leaveAsRepoApprover.value,
        RequestType.grantRepoAccess.value, RequestType.removeRepoAccess.value
    ]:
        return 'repo'

    if requestType in [
        RequestType.grantDocAccess.value
    ]:
        return 'doc'

    raise Exception('Unexpected Request Type: {}'.format(requestType))
