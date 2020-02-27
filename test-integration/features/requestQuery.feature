Feature: As a user I want to query my requests

  Scenario: User has no requests in the system
    Given backend app is setup
    When i am logged in as sam@example.com
    And i GET "/requests/"
    Then i should get response with status code 200 and data
      """
      []
      """

  Scenario: User queries all requests
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    When i submit request of type joinAccount for 'Joe Car Hire'
    And i GET "/requests/"
    Then i should get response with status code 200 and data
      """
      [
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
      ]
      """

  Scenario: User queries all pending requests
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    When i submit request of type joinAccount for 'Joe Car Hire'
    And i GET "/requests/?status=pending"
    Then i should get response with status code 200 and data
      """
      [
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
      ]
      """

  Scenario: User queries request with incorrect status
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
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
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as kevin@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@example.com
    And i GET "/requests/?status=pending"
    Then i should get response with status code 200 and data
      """
      [
        {
          "requestId": "***",
          "accountId": "***",
          "accountName": "Joe Car Hire",
          "requestee": "5088a9ccd13fb54ea384c0b63076a001",
          "requesteeEmail": "kevin@example.com",
          "requestor": "5088a9ccd13fb54ea384c0b63076a001",
          "requestorEmail": "kevin@example.com",
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
      ]
      """

  Scenario: Owner queries all archived requests
    Given backend app is setup
    And i am logged in as joe@example.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as kevin@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@example.com
    And i mark last_submitted request as approved
    And i GET "/requests/?status=archived"
    Then i should get response with status code 200 and data
      """
      [
        {
          "requestId": "***",
          "accountId": "***",
          "accountName": "Joe Car Hire",
          "requestee": "5088a9ccd13fb54ea384c0b63076a001",
          "requestor": "5088a9ccd13fb54ea384c0b63076a001",
          "requesteeEmail": "kevin@example.com",
          "requestorEmail": "kevin@example.com",
          "requestType": "joinAccount",
          "requestedOnResource": "***",
          "requestedOnResourceName": "Joe Car Hire",
          "status": "approved",
          "createdAt": "***",
          "updateHistory": [
            {
              "action": "approved",
              "updatedBy": "f5b8fb60c6116331da07c65b96a8a1d1",
              "updatedByEmail": "joe@example.com",
              "updatedAt": "***"
            }
          ]
        }
      ]
      """
