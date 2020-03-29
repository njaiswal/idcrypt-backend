Feature: User creates new repo

  Scenario Outline: POST repos/ api is called with various payloads
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i submit create repo request with '<payload>'
    Then i get response with '<status_code>' and '<message>'

    Examples:
      | payload                                                         | status_code | message                                                                                        |
      | { "name": null,  "desc": "My Repo 1",  "retention": 30 }        | 400         | {"schema_errors": { "name": ["Field may not be null."]}}                                       |
      | { "name": "`ls`",  "desc": "My Repo 1",  "retention": 30 }      | 400         | {"schema_errors": { "name": ["Repo name must not contain special characters."]}}               |
      | { "name": "R1",  "desc": "My Repo 1",  "retention": 30 }        | 400         | {"schema_errors": { "name": ["Length must be between 3 and 30."]}}                             |
      | { "desc": "My Repo 1",  "retention": 30 }                       | 400         | {"schema_errors": { "name": ["Missing data for required field."]}}                             |
      | { "name": "My Repo",  "desc": "12",  "retention": 30 }          | 400         | {"schema_errors": { "desc": ["Length must be between 3 and 30."]}}                             |
      | { "name": "REPO",  "desc": "`ls`",  "retention": 30 }           | 400         | {"schema_errors": { "desc": ["Repo description must not contain special characters."]}}        |
      | { "name": "REPO",  "desc": "DES",  "retention": 0 }             | 400         | {"schema_errors": { "retention": ["Retention period should be between 30 days and 5 years."]}} |
      | { "name": "REPO",  "desc": "DES",  "retention": 31, "xx": "y" } | 400         | {"schema_errors": {  "xx": ["Unknown field."]}}                                                |

  Scenario: New User with no account tries to create a repo
    Given backend app is setup
    When i am logged in as sam@jrn-limited.com
    And i submit create repo request with '{ "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Only owners and admins of account can create a new repository."
      }
      """

  Scenario: Non-Owner user tries to create a repo
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
    And i submit create repo request with '{ "name": "My Repo 2",  "desc": "My Repo 2",  "retention": 30 }'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Only owners and admins of account can create a new repository."
      }
      """

  Scenario: Owner can creates new repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    When i submit create repo request with '{"name": "My Repo 2",  "desc": "My Repo 2",  "retention": 30 }'
    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "****",
        "name": "My Repo 2",
        "desc": "My Repo 2",
        "retention": 30,
        "approvers": [
          "joe@jrn-limited.com"
        ],
        "users": [
          "joe@jrn-limited.com"
        ],
        "createdAt": "***"
      },
      {
        "repoId": "***",
        "accountId": "***",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          "joe@jrn-limited.com"
        ],
        "users": [
          "joe@jrn-limited.com"
        ],
        "createdAt": "***"
      }
    ]
    """
    And s3 bucket for account 'Joe Car Hire' is available
    And repo meta info file 'my-repo-1/metaInfo.txt' is available for account 'Joe Car Hire'
    And repo meta info file 'my-repo-2/metaInfo.txt' is available for account 'Joe Car Hire'


  Scenario: Owner tries to create repo with same name
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200
    When i submit create repo request with '{"name": "My Repo 1",  "desc": "My Repo 2",  "retention": 30 }'
    Then i should get response with status code 400 and data
    """
    {
      "message": "Repository with name 'My Repo 1' already exists."
    }
    """

  Scenario: Owner can creates new repo, test rollback
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And s3 logging bucket is missing
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 500 and data
    """
    {
      "message": "New account creation failed. Please try again."
    }
    """
    And account with name 'Joe Car Hire' is not present
