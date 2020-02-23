Feature: As a user I want to use account/ api

  Scenario: account/ api called with a very short name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name x
    Then i should get response with status code 400 and data
      """
      {
        "schema_errors": {
          "name": [
            "Length must be between 3 and 30."
          ]
        }
      }
      """

  Scenario: account/ api called with a special characters in name name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name 1=1
    Then i should get response with status code 400 and data
      """
      {
        "schema_errors": {
          "name": [
            "Account name must not contain special characters."
          ]
        }
      }
      """

  Scenario: account/ api called without a name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account without a name
    Then i should get response with status code 400 and data
      """
      {
        "schema_errors": {
          "name": [
            "Field may not be null."
          ]
        }
      }
      """

  Scenario: user calls account/ with a name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """

  Scenario: user tries to call account/ twice with same name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
    And i create a new account with name Joe Car Hire
    Then i should get response with status code 417 and data
      """
      {
        "message": "Account name 'Joe Car Hire' already exists. Please choose another name."
      }
      """

  Scenario: user tries to call account/ twice with different name
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
    And i create a new account with name Joe Other Car Hire
    Then i should get response with status code 417 and data
      """
      {
        "message": "You are already marked as owner of another account."
      }
      """

  Scenario: User tries to update account status of a account he does not own
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
    When i am logged in as kevin@example.com
    And i deactivate account 'Joe Car Hire'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Only owner of account allowed to update the account."
      }
      """

  Scenario: User tries to update account status of a account that does not exists
    Given backend app is setup
    And i am logged in as kevin@example.com
    When i deactivate accountId '12345-6789-1111'
    Then i should get response with status code 404 and data
      """
      {
        "message": "Account Id not found."
      }
      """

  Scenario: Owner tries to update account status without '?status=inactive' query parameter
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
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
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
    And i activate account 'Joe Car Hire'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Status is already set to active."
      }
      """

  Scenario: Owner can deactivate and activate account
    Given backend app is setup
    And i am logged in as joe@example.com
    When i create a new account with name Joe Car Hire
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
        "createdAt": "***"
      }
      """
    And i deactivate account 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "accountId": "***",
        "name": "Joe Car Hire",
        "owner": "f5b8fb60c6116331da07c65b96a8a1d1",
        "domain": "example.com",
        "address": null,
        "email": "joe@example.com",
        "status": "inactive",
        "tier": "free",
        "createdAt": "***"
      }
      """
    When i activate account 'Joe Car Hire'
    Then i should get response with status code 200 and data
      """
      {
        "accountId": "****",
        "name": "Joe Car Hire",
        "owner": "f5b8fb60c6116331da07c65b96a8a1d1",
        "domain": "example.com",
        "address": null,
        "email": "joe@example.com",
        "status": "active",
        "tier": "free",
        "createdAt": "***"
      }
      """
