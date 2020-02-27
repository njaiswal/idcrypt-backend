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
