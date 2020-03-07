Feature: As a user I want to query my requests

  Scenario: User has no requests in the system
    Given backend app is setup
    When i am logged in as sam@jrn-limited.com
    And i GET "/requests/"
    Then i should get response with status code 200 and data
      """
      []
      """

  Scenario: User queries all requests
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    When i submit request of type joinAccount for 'Joe Car Hire'
    And i GET "/requests/"
    Then i should get response with status code 200 and data
      """
      [
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
      ]
      """

  Scenario: User queries all pending requests
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    When i submit request of type joinAccount for 'Joe Car Hire'
    And i GET "/requests/?status=pending"
    Then i should get response with status code 200 and data
      """
      [
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
      ]
      """

  Scenario: User queries request with incorrect status
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    When i submit request of type joinAccount for 'Joe Car Hire'
    And i GET "/requests/?status=xyz"
    Then i should get response with status code 422 and data
      """
      {
        "errors": {
          "status": [
            "Must be one of: pending, approved, denied, failed, cancelled, archived."
          ]
        }
      }
      """

  Scenario: Owner queries all pending requests
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i GET "/requests/?status=pending"
    Then i should get response with status code 200 and data
      """
      [
        {
          "requestId": "***",
          "accountId": "***",
          "accountName": "Joe Car Hire",
          "requestee": "85ee1019-9c53-4da4-a749-b9714f301155",
          "requesteeEmail": "kevin@jrn-limited.com",
          "requestor": "85ee1019-9c53-4da4-a749-b9714f301155",
          "requestorEmail": "kevin@jrn-limited.com",
          "requestType": "joinAccount",
          "requestedOnResource": "***",
          "requestedOnResourceName": "Joe Car Hire",
          "status": "pending",
          "createdAt": "***",
          "updateHistory": []
        },
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
      ]
      """

  Scenario: Owner queries all archived requests
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    And i GET "/requests/?status=archived"
    Then i should get response with status code 200 and data
      """
      [
        {
          "requestId": "***",
          "accountId": "***",
          "accountName": "Joe Car Hire",
          "requestee": "85ee1019-9c53-4da4-a749-b9714f301155",
          "requestor": "85ee1019-9c53-4da4-a749-b9714f301155",
          "requesteeEmail": "kevin@jrn-limited.com",
          "requestorEmail": "kevin@jrn-limited.com",
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
