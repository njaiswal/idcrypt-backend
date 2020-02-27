Feature: As a user I want to use account/ api

  Scenario Outline: account/ api called with various payloads
    Given backend app is setup
    And i am logged in as joe@example.com
    When i submit create account request with '<payload>'
    Then i get response with '<status_code>' and '<message>'

    Examples:
      | payload                                                                                   | status_code | message                                                                                                 |
      | { "name": null, "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}  | 400         | {"schema_errors": { "name": ["Field may not be null."]}}                                                |
      | { "name": "1=1", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }} | 400         | {"schema_errors": { "name": ["Account name must not contain special characters."]}}                     |
      | { "name": "x", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}   | 400         | {"schema_errors": { "name": ["Length must be between 3 and 30."]}}                                      |
      | { "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}                | 400         | {"schema_errors": { "name": ["Missing data for required field."]}}                                      |
      | { "name": "ABC", "repo": { "name": "x",  "desc": "My Repo 1",  "retention": 30 }}         | 400         | {"schema_errors": { "repo": { "name": ["Length must be between 3 and 30."]}}}                           |
      | { "name": "ABC", "repo": { "name": "REPO",  "desc": "`ls`",  "retention": 30 }}           | 400         | {"schema_errors": { "repo": { "desc": ["Repo description must not contain special characters."]}}}      |
      | { "name": "ABC", "repo": { "name": "REPO",  "desc": "DES",  "retention": 0 }}             | 400         | {"schema_errors": { "repo": { "retention": ["Retention period should be between 1 day and 5 years."]}}} |
      | { "name": "ABC", "repo": { "name": "REPO",  "desc": "DES",  "retention": 1, "xx": "y" }}  | 400         | {"schema_errors": { "repo": { "xx": ["Unknown field."]}}}                                               |

    @dev
  Scenario: user creates new account
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
    When i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "***",
        "name": "Docs",
        "desc": "KYC",
        "retention": 30,
        "approvers": [
          "f5b8fb60c6116331da07c65b96a8a1d1"
        ],
        "users": [
          "f5b8fb60c6116331da07c65b96a8a1d1"
        ],
        "createdAt": "***"
      }
    ]
    """
    And s3 bucket for account 'Joe Car Hire' is available
    And repo meta info file 'Docs/metaInfo.txt' is available for account 'Joe Car Hire'

  # Following test is commented out since it takes a very long time to run and will test functionality only half the times
  # We need a better way of mocking method responses when tests are running
  # There seems to be a mock, patch way to do it for a scenario. todo
#  Scenario: user account gets created even when there is a s3 bucket name clash
#    Given backend app is setup
#    And s3 bucket namespace for 'Joe_Car_Hire' is exhausted
#    And i am logged in as joe@example.com
#    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
#    Then i should get response with status code 200
#    And s3 bucket for account 'Joe Car Hire' is available


  Scenario: user tries to call account/ twice with same name
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
    And i create a new account with payload
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
    Then i should get response with status code 400 and data
      """
      {
        "message": "Account name 'Joe Car Hire' already exists. Please choose another name."
      }
      """

  Scenario: user tries to call account/ twice with different name
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
    And i create a new account with payload
      """
      {
        "name": "Joe Car Shop",
        "repo": {
          "name": "Docs",
          "desc": "KYC",
          "retention": 30
        }
      }
      """
    Then i should get response with status code 400 and data
      """
      {
        "message": "You are already marked as owner of another account."
      }
      """
