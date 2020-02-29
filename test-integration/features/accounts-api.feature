Feature: As a user I want to use accounts/ api

  Scenario: New user with new unknown domain calls accounts/
    Given backend app is setup
    And i am logged in as joe@example.com
    When i GET "/accounts/"
    Then i should get response with status code 200 and data
      """
      []
      """

  Scenario: Owner calls accounts/
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with payload
      """
      {
        "name": "Joe Car Hire",
        "repo": {
          "name": "Docs",
          "desc": "KYC",
          "retention": 30
        }
      }
      """
    Then i should get response with status code 200 and data
      """
      {
        "accountId": "***",
        "name": "Joe Car Hire",
        "owner": "f5b8fb60c6116331da07c65b96a8a1d1",
        "domain": "example.com",
        "address": null,
        "email": "joe@example.com",
        "status": "active",
        "tier": "free",
        "createdAt": "***",
        "members": ["f5b8fb60c6116331da07c65b96a8a1d1"],
        "admins": []
      }
      """
    When i GET "/accounts/"
    Then i should get response with status code 200 and data
      """
      [
        {
          "accountId": "***",
          "name": "Joe Car Hire",
          "owner": "f5b8fb60c6116331da07c65b96a8a1d1",
          "domain": "example.com",
          "address": null,
          "email": "joe@example.com",
          "status": "active",
          "tier": "free",
          "createdAt": "***",
          "members": ["f5b8fb60c6116331da07c65b96a8a1d1"],
          "admins": []
        }
      ]
      """

  Scenario: Account member calls accounts/
    Given backend app is setup
    And i am logged in as joe@example.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    When i am logged in as sam@example.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@example.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    When i am logged in as sam@example.com
    And i GET "/accounts/"
    Then i should get response with status code 200 and data
      """
      [
        {
          "accountId": "0b521176-65b4-4a68-88be-dc5ca33b6e74",
          "name": "Joe Car Hire",
          "owner": "f5b8fb60c6116331da07c65b96a8a1d1",
          "domain": "example.com",
          "address": null,
          "email": "joe@example.com",
          "status": "active",
          "tier": "free",
          "members": [
            "f5b8fb60c6116331da07c65b96a8a1d1",
            "e179e95c00e7718ab4a23840f992ea63"
          ],
          "admins": [],
          "createdAt": "2020-02-28 20:21:13.763796"
        }
      ]
      """
