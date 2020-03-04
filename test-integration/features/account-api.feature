Feature: As a user I want to use account/ api

  # Dummy scenario to flush out any TrimmedDataAccessException that requestProcessor might get
  Scenario: User can cancel self request
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    And i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i mark joinAccount request as cancelled
    Then i should get response with status code 200

  Scenario Outline: account/ api called with various payloads
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
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

  Scenario: user creates new account
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
    And repo meta info file 'Docs/metaInfo.txt' is available for account 'Joe Car Hire'

  # Following test is commented out since it takes a very long time to run and will test functionality only half the times
  # We need a better way of mocking method responses when tests are running
  # There seems to be a mock, patch way to do it for a scenario. todo
#  Scenario: user account gets created even when there is a s3 bucket name clash
#    Given backend app is setup
#    And s3 bucket namespace for 'Joe_Car_Hire' is exhausted
#    And i am logged in as joe@jrn-limited.com
#    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
#    Then i should get response with status code 200
#    And s3 bucket for account 'Joe Car Hire' is available


  Scenario: user tries to call account/ twice with same name
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

  Scenario: Non users tries to get account membership
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Main Account", "repo": { "name": "UK KYC",  "desc": "Customer kyc docs",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i get account membership for account name 'Joe Main Account'
    Then i should get response with status code 403 and data
      """
      {
        "message": "Only members of account allowed to get account membership details."
      }
      """


  Scenario: Member gets account membership
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "Customer kyc docs",  "retention": 30 }}'
    Then i should get response with status code 200

    # Add 3 members
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as bob@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Make sam repo approver
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAsRepoApprover for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Grant sam repo access
    When i am logged in as sam@jrn-limited.com
    And i submit request of type grantRepoAccess for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Grant kevin repo access
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type grantRepoAccess for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Now sam get account membership
    When i get account membership for account name 'Joe Car Hire'
    Then i should get response with status code 200 and data
    """
    [
      {
        "email": "joe@jrn-limited.com",
        "email_verified": "true",
        "repoAccess": [
          "My Repo 1"
        ],
        "repoApprover": [
          "My Repo 1"
        ]
      },
      {
        "email": "sam@jrn-limited.com",
        "email_verified": "true",
        "repoAccess": [
          "My Repo 1"
        ],
        "repoApprover": [
          "My Repo 1"
        ]
      },
      {
        "email": "kevin@jrn-limited.com",
        "email_verified": "true",
        "repoAccess": [
          "My Repo 1"
        ],
        "repoApprover": []
      },
      {
        "email": "bob@jrn-limited.com",
        "email_verified": "true",
        "repoAccess": [],
        "repoApprover": []
      }
    ]
    """
