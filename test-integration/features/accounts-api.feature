Feature: As a user I want to use accounts/ api

  Scenario: Options request contains correct CORS headers
    Given backend app is setup
    And i am logged in as joe@jrn-limited
    And i OPTIONS "/accounts/"
    Then i should get response with status code 200 and headers
    """
    {
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Origin": "http://localhost:4200",
        "Allow": "GET, OPTIONS, HEAD",
        "Content-Length": "0",
        "Content-Type": "text/html; charset=utf-8",
        "Vary": "Origin"
    }
    """

  Scenario: New user with new unknown domain calls accounts/
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i GET "/accounts/"
    Then i should get response with status code 200 and data
      """
      []
      """

  Scenario: Owner calls accounts/
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
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
        "owner": "joe@jrn-limited.com",
        "domain": "jrn-limited.com",
        "address": null,
        "email": "joe@jrn-limited.com",
        "status": "active",
        "tier": "free",
        "createdAt": "***",
        "members": ["joe@jrn-limited.com"],
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
          "owner": "joe@jrn-limited.com",
          "domain": "jrn-limited.com",
          "address": null,
          "email": "joe@jrn-limited.com",
          "status": "active",
          "tier": "free",
          "createdAt": "***",
          "members": ["joe@jrn-limited.com"],
          "admins": []
        }
      ]
      """

  Scenario: Account member calls accounts/
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    When i am logged in as sam@jrn-limited.com
    And i GET "/accounts/"
    Then i should get response with status code 200 and data
      """
      [
        {
          "accountId": "0b521176-65b4-4a68-88be-dc5ca33b6e74",
          "name": "Joe Car Hire",
          "owner": "joe@jrn-limited.com",
          "domain": "jrn-limited.com",
          "address": null,
          "email": "joe@jrn-limited.com",
          "status": "active",
          "tier": "free",
          "members": [
            "joe@jrn-limited.com",
            "sam@jrn-limited.com"
          ],
          "admins": [],
          "createdAt": "2020-02-28 20:21:13.763796"
        }
      ]
      """
