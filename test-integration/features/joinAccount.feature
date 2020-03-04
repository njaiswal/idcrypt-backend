Feature: As a user I want to join/leave a account

  Scenario: User submits an account joining request for Account with same domain
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "requestId": "***",
        "accountId": "***",
        "accountName": "Joe Car Hire",
        "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "requesteeEmail": "sam@jrn-limited.com",
        "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "requestorEmail": "sam@jrn-limited.com",
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
    And i am logged in as joe@jrn-limited.com
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
    And i am logged in as joe@jrn-limited.com
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
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
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
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type makeMeGod for 'Joe Car Hire'
    Then i should get response with status code 400 and data
      """
      {
        "schema_errors": {
          "requestType": [
            "Must be one of: joinAccount, leaveAccount, joinAsRepoApprover, leaveAsRepoApprover, grantRepoAccess, removeRepoAccess."
          ]
        }
      }
      """

  Scenario: User submits an account joining request with unknown accountId
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of requestType: 'joinAccount', accountId: '12345-12345-12345', requestedOnResource: '12345-12345-12345'
    Then i should get response with status code 404 and data
      """
      {
        "message": "Account ID not found"
      }
      """

  Scenario: User submits an account joining request where requestedOnResourceResource not equal accountId
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of requestType: 'joinAccount', accountId: 'last_created_accountId', requestedOnResource: '9999-9999-9999'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Malformed payload. Resource does not belong to accountId"
      }
      """

  Scenario: User tries to raise joinAccount request on 2 accounts
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as kevin@jrn-limited.com
    And i submit create account request with '{ "name": "Kevin Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    And i submit request of type joinAccount for 'Kevin Car Hire'
    Then i should get response with status code 400 and data
    """
    {
      "message": "Similar request already exists. Please cancel it to raise a new one."
    }
    """

  Scenario: Member of a account tries to submit joinAccount request for another account
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    And i am logged in as keving@jrn-limited.com
    When i submit create account request with '{ "name": "Kevin Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Kevin Car Hire'

    Then i should get response with status code 400 and data
      """
      {
        "message" : "You are already a member of another Account"
      }
      """

