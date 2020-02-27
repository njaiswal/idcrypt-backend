Feature: As a user I want to join/leave a account

  Scenario: User submits an account joining request for Account with same domain
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "requestId": "***",
        "accountId": "***",
        "accountName": "Joe Car Hire",
        "requestee": "e179e95c00e7718ab4a23840f992ea63",
        "requesteeEmail": "sam@example.com",
        "requestor": "e179e95c00e7718ab4a23840f992ea63",
        "requestorEmail": "sam@example.com",
        "requestType": "joinAccount",
        "requestedOnResource": "***",
        "requestedOnResourceName": "Joe Car Hire",
        "status": "pending",
        "createdAt": "***",
        "updateHistory": []
      }
      """

  Scenario: User submits an account joining request for Account with different domain
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@xyz.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    Then i should get response with status code 403 and data
      """
      {
        "message": "User cannot submit a request to join a account with different domain."
      }
      """

  Scenario: Owner submits an account joining request for a Account
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    And i submit request of type joinAccount for 'Joe Car Hire'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Owners of account are not allowed to raise join Account requests for self."
      }
      """

  Scenario: User submits an account joining request for Account twice
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    And i submit request of type joinAccount for 'Joe Car Hire'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Similar request already exists. Please cancel it to raise a new one."
      }
      """

  Scenario: User submits an account joining request with bad payload
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type makeMeGod for 'Joe Car Hire'
    Then i should get response with status code 400 and data
      """
      {
        "schema_errors": {
          "requestType": [
            "Must be one of: suspendAccount, deleteAccount, joinAccount, leaveAccount, joinAsAccountAdmin, leaveAsAccountAdmin, joinAsApprovers, leaveAsApprover, joinAsRepoUser, leaveAsRepoUser."
          ]
        }
      }
      """

  Scenario: User submits an account joining request with unknown accountId
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of requestType: 'joinAccount', accountId: '12345-12345-12345', requestedOnResource: '12345-12345-12345'
    Then i should get response with status code 404 and data
      """
      {
        "message": "accountId not found"
      }
      """

  Scenario: User submits an account joining request where requestedOnResourceResource not equal accountId
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of requestType: 'joinAccount', accountId: 'last_created_accountId', requestedOnResource: '9999-9999-9999'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Malformed payload. Resource does not belong to accountId"
      }
      """

  Scenario: User tries to raise joinAccount request on 2 accounts
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as kevin@example.com
    And i submit create account request with '{ "name": "Kevin Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    And i submit request of type joinAccount for 'Kevin Car Hire'
    Then i should get response with status code 400 and data
    """
    {
      "message": "Similar request already exists. Please cancel it to raise a new one."
    }
    """
