Feature: User creates new doc

  Scenario Outline: POST docs/ api is called with various payloads
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i submit create doc request with '<payload>'
    Then i get response with '<status_code>' and '<message>'

    Examples:
      | payload                                                                      | status_code | message                                                                  |
      | { "accountId": null,  "repoId": "My Repo 1", "name": "Cust One" }            | 400         | {"schema_errors": { "accountId": ["Field may not be null."]}}            |
      | { "repoId": "My Repo 1", "name": "Cust One" }                                | 400         | {"schema_errors": { "accountId": [ "Missing data for required field."]}} |
      | { "accountId": "xxxxxx",  "repoId": "My", "name": "Cust One" }               | 400         | {"schema_errors": { "repoId": ["Shorter than minimum length 3."]}}       |
      | { "accountId": "xxxxxx",  "repoId": "xxxx", "yy": "aa", "name": "Cust One" } | 400         | {"schema_errors": { "yy": ["Unknown field."]}}                           |
      | { "accountId": "xxxxx",  "repoId": "My Repo 1", "name": null }               | 400         | {"schema_errors": { "name": ["Field may not be null."]}}                 |

  Scenario: New User with no account membership tries to create a doc
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with '{ "accountId": "last_created_accountId",  "repoId": "xxxx", "name": "Sam" }'
    Then i should get response with status code 403 and data
    """
    {
      "message": "Not Authorized."
    }
    """

  Scenario: User without Repo User Role tries to create a doc
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
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Cust One'
    Then i should get response with status code 403 and data
    """
    {
      "message": "Only Account members having Repository Access Role have access to repository."
    }
    """

  Scenario: User with Repo User Role tries to create a doc
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
    And i submit request of type grantRepoAccess for account 'Joe Car Hire' and repo 'My Repo 1'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Customer One'
    Then i should get response with status code 200 and data
    """
    {
      "docId": "***",
      "repoId": "***",
      "accountId": "***",
      "retention": 30,
      "status": "initialized",
      "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "uploadedByEmail" : null,
      "downloadableBy": ["30accff5-916d-47d7-bdbb-a3d7dc95feec"],
      "downloadable": false,
      "docType": null,
      "text": null,
      "name" : "Customer One",
      "createdAt": "***",
      "errorMessage": null
    }
    """
