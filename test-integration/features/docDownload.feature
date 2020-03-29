Feature: Doc Download

  Scenario Outline: User tries to download doc with various inputs and gets error message
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Kevin joins the account
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Capture accountId and repoId in test context
    When i am logged in as joe@jrn-limited.com
    And i GET "/repos/"
    Then i should get response with status code 200

    # User tries to download doc
    When i am logged in as <user>@jrn-limited.com
    When i try to download doc with accountId: '<accountId>' repoId: '<repoId>' docId: '<docId>'
    Then i should get response with status code <status> and data
    """
    {
       "message": "<message>"
    }
    """
    Examples:
      | user  | accountId            | repoId            | docId     | status | message                                                                       |
      | sam   | 1234-1234            | 1234-1234         | 1234-1234 | 404    | Account not found.                                                            |
      | sam   | last_saved_accountId | 1234-1234         | 1234-1234 | 403    | Not Authorized.                                                               |
      | kevin | last_saved_accountId | 12345-1234        | 1234-1234 | 404    | Repository not found.                                                         |
      | kevin | last_saved_accountId | last_saved_repoId | 1234-1234 | 403    | Only Account members having Repository Access Role have access to repository. |
      | joe   | last_saved_accountId | last_saved_repoId | 1234-1234 | 404    | Document not found.                                                           |

  Scenario: User tries to download a doc where user does not have Doc Access Role
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Sam joins the account
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Sam gets repo Access
    When i am logged in as sam@jrn-limited.com
    And i submit request of type grantRepoAccess for account 'Joe Car Hire' and repo 'My Repo 1'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Joe uploads a file with correct repoId and docId
    When i am logged in as joe@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Lucy Gale'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Capture accountId, repoId and docId
    When i am logged in as joe@jrn-limited.com
    And i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200

    # Sam tries to download doc
    When i am logged in as sam@jrn-limited.com
    When i try to download doc with accountId: 'last_saved_accountId' repoId: 'last_saved_repoId' docId: 'last_saved_docId'
    Then i should get response with status code 403 and data
    """
    {
       "message": "Not Authorized."
    }
    """


  Scenario: Owner tries to download a doc
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Joe uploads a file with correct repoId and docId
    When i am logged in as joe@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Lucy Gale'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Capture accountId, repoId and docId
    When i am logged in as joe@jrn-limited.com
    And i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200

    # Joe tries to download doc
    When i am logged in as joe@jrn-limited.com
    When i try to download doc with accountId: 'last_saved_accountId' repoId: 'last_saved_repoId' docId: 'last_saved_docId'
    Then i should get response with status code 200 and data
    """
    {
      "name": "Lucy_Gale_drivingLicence.jpg",
      "contentType": "image/jpeg"
    }
    """

  Scenario: User's doc access request gets approved by a approver and then downloads the doc
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Sam joins the account
    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Sam gets repo Access
    When i am logged in as sam@jrn-limited.com
    And i submit request of type grantRepoAccess for account 'Joe Car Hire' and repo 'My Repo 1'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # kevin joins the account
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # kevin gets repo Approver
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAsRepoApprover for account 'Joe Car Hire' and repo 'My Repo 1'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Sam uploads a file with correct repoId and docId
    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Lucy Gale'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Sam searches for the uploaded doc without any text
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200

    # Sam raises request to download above document
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId#last_created_docId'
    Then i should get response with status code 200

    # Kevin approves the request
    When i am logged in as kevin@jrn-limited.com
    And i mark last_submitted request as approved
    Then i should get response with status code 200
    And i wait for last_submitted request to get 'closed'

    # Sam queries for downloadable documents
    When i am logged in as sam@jrn-limited.com
    When i query downloadable docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200

    # Sam tries to download the doc
    When i am logged in as sam@jrn-limited.com
    And i try to download doc with accountId: 'last_saved_accountId' repoId: 'last_saved_repoId' docId: 'last_saved_docId'
    Then i should get response with status code 200 and data
    """
    {
      "name": "Lucy_Gale_drivingLicence.jpg",
      "contentType": "image/jpeg"
    }
    """
