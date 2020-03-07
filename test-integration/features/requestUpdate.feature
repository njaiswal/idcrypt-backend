Feature: As a user I want to update my requests

  Scenario: User can cancel self request
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i mark joinAccount request as cancelled
    Then i should get response with status code 200 and data
    """
    {
      "requestId": "***",
      "accountId": "***",
      "accountName": "Joe Car Hire",
      "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requesteeEmail": "sam@jrn-limited.com",
      "requestorEmail": "sam@jrn-limited.com",
      "requestType": "joinAccount",
      "requestedOnResource": "4ac4b5cf-4b16-4092-8e45-1cb05b390df8",
      "requestedOnResourceName": "Joe Car Hire",
      "status": "cancelled",
      "createdAt": "2020-02-21 15:17:35.676757",
      "updateHistory": [
        {
          "action": "cancelled",
          "updatedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
          "updatedByEmail": "sam@jrn-limited.com",
          "updatedAt": "***"
        }
      ]
    }
    """

  Scenario: User cancels self request twice
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i mark joinAccount request as cancelled
    When i mark joinAccount request as cancelled
    Then i should get response with status code 400 and data
    """
    {
      "message" : "Request status already marked as cancelled."
    }
    """

  Scenario: Owner can approve joinAccount request
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as approved
    Then i should get response with status code 200 and data
    """
    {
      "requestId": "***",
      "accountId": "***",
      "accountName": "Joe Car Hire",
      "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requesteeEmail": "sam@jrn-limited.com",
      "requestorEmail": "sam@jrn-limited.com",
      "requestType": "joinAccount",
      "requestedOnResource": "4ac4b5cf-4b16-4092-8e45-1cb05b390df8",
      "requestedOnResourceName": "Joe Car Hire",
      "status": "approved",
      "createdAt": "2020-02-21 15:17:35.676757",
      "updateHistory": [
        {
          "action": "approved",
          "updatedBy": "f5b8fb60c6116331da07c65b96a8a1d1",
          "updatedByEmail": "joe@jrn-limited.com",
          "updatedAt": "***"
        }
      ]
    }
    """
    And i wait for last_submitted request to get 'closed'
    When i am logged in as sam@jrn-limited.com
    And i GET "/requests/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "requestId": "***",
        "accountId": "***",
        "accountName": "Joe Car Hire",
        "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "requesteeEmail": "sam@jrn-limited.com",
        "requestorEmail": "sam@jrn-limited.com",
        "requestType": "joinAccount",
        "requestedOnResource": "***",
        "requestedOnResourceName": "Joe Car Hire",
        "status": "closed",
        "createdAt": "***",
        "updateHistory": [
          {
            "action": "approved",
            "updatedBy": "f5b8fb60c6116331da07c65b96a8a1d1",
            "updatedByEmail": "joe@jrn-limited.com",
            "updatedAt": "***"
          },
          {
            "action": "closed",
            "updatedBy": "007",
            "updatedByEmail": "automation@idcrypt.io",
            "updatedAt": "***"
          }
        ]
      }
    ]
    """

  Scenario: Owner can deny joinAccount request
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as denied
    Then i should get response with status code 200 and data
    """
    {
      "requestId": "***",
      "accountId": "***",
      "accountName": "Joe Car Hire",
      "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requesteeEmail": "sam@jrn-limited.com",
      "requestorEmail": "sam@jrn-limited.com",
      "requestType": "joinAccount",
      "requestedOnResource": "4ac4b5cf-4b16-4092-8e45-1cb05b390df8",
      "requestedOnResourceName": "Joe Car Hire",
      "status": "denied",
      "createdAt": "2020-02-21 15:17:35.676757",
      "updateHistory": [
        {
          "action": "denied",
          "updatedBy": "f5b8fb60c6116331da07c65b96a8a1d1",
          "updatedByEmail": "joe@jrn-limited.com",
          "updatedAt": "***"
        }
      ]
    }
    """

  Scenario: Non-existing requestId sent in request update payload
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i try to mark accountId=last_created_accountId and requestId=12345-12345-12345-12345 as approved
    Then i should get response with status code 404 and data
    """
    {
      "message": "Request not found."
    }
    """

  Scenario: Non-existing accountId sent in request update payload
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i try to mark accountId=12345-12345-12345 and requestId=12345-12345-12345-12345 as approved
    Then i should get response with status code 404 and data
    """
    {
      "message": "Request not found."
    }
    """

  Scenario: Owner tries to mark pending request straight to closed
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as closed
    Then i should get response with status code 400 and data
    """
    {
      "message": "Users cannot mark requests as closed."
    }
    """

  Scenario: Owner tries to mark cancelled request approved
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    And i mark joinAccount request as cancelled
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as approved
    Then i should get response with status code 400 and data
    """
    {
      "message": "Invalid request status change: cancelled->approved"
    }
    """

  Scenario: Owner tries to mark approved request approved again
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as approved
    And i mark joinAccount request as approved
    Then i should get response with status code 400

  Scenario: Owner tries to mark approved request as closed
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark joinAccount request as approved
    And i mark joinAccount request as closed
    Then i should get response with status code 400 and data
    """
    {
      "message": "Users cannot mark requests as closed."
    }
    """

  Scenario: Owner of another account tries to mark a request as approved in another account
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as mark@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as mark@jrn-limited.com
    And i mark last_submitted request as approved
    Then i should get response with status code 403 and data
    """
    {
      "message": "Not Authorized."
    }
    """

