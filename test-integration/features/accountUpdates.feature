Feature: Account update actions are performed

  Scenario: User tries to update account status of a account he does not own
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    When i am logged in as kevin@jrn-limited.com
    And i deactivate account 'Joe Car Hire'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Only owner of account allowed to update the account."
      }
      """

  Scenario: User tries to update account status of a account that does not exists
    Given backend app is setup
    And i am logged in as kevin@jrn-limited.com
    When i deactivate accountId '12345-6789-1111'
    Then i should get response with status code 404 and data
      """
      {
        "message": "Account Id not found."
      }
      """

  Scenario: Owner tries to update account status without '?status=inactive' query parameter
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    And i update account 'Joe Car Hire' with query parameter xxxx=inactive
    Then i should get response with status code 400 and data
      """
      {
        "message": "Invalid account update."
      }
      """
    And i update account 'Joe Car Hire' with query parameter status=ttttt
    Then i should get response with status code 422 and data
      """
      {
        "errors": {
          "status": [
            "Must be one of: active, inactive."
          ]
        }
      }
      """

  Scenario: Owner tries to update account status to active when its already active
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    And i activate account 'Joe Car Hire'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Status is already set to active."
      }
      """

  Scenario: Owner can deactivate and activate account
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    And i deactivate account 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "accountId": "***",
        "name": "Joe Car Hire",
        "owner": "joe@jrn-limited.com",
        "domain": "jrn-limited.com",
        "address": null,
        "email": "joe@jrn-limited.com",
        "status": "inactive",
        "tier": "free",
        "createdAt": "***",
        "members": ["joe@jrn-limited.com"],
        "admins": []
      }
      """
    When i activate account 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "accountId": "****",
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
