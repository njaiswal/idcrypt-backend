Feature: Doc Download requests

  Scenario: User raises grantDocAccess request where user is not account member
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Capture accountId and repoId in test context
    When i am logged in as joe@jrn-limited.com
    And i GET "/repos/"
    Then i should get response with status code 200

    # Sam raises grantDocAccess Request
    When i am logged in as sam@jrn-limited.com
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId#1234-1234'
    Then i should get response with status code 403 and data
    """
    {
       "message": "Only owner and members of account can raise request of type grantDocAccess"
    }
    """

  Scenario: User raises grantDocAccess request with mal-formed requestedOnResource
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

    # Sam raises grantDocAccess Request
    When i am logged in as joe@jrn-limited.com
    And i GET "/repos/"
    When i am logged in as sam@jrn-limited.com
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId'
    Then i should get response with status code 400 and data
    """
    {
       "message": "Malformed payload"
    }
    """

  Scenario: User raises grantDocAccess request with docId which is not present
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

    # Sam raises grantDocAccess Request
    When i am logged in as joe@jrn-limited.com
    And i GET "/repos/"
    When i am logged in as sam@jrn-limited.com
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId#xxxx-yyyy'
    Then i should get response with status code 404 and data
    """
    {
       "message": "Document not found"
    }
    """

  Scenario: User can raise doc download request. And members will no Repo Access cannot.
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
    Then i should get response with status code 200 and data
    """
    {
      "requestId": "****",
      "accountId": "****",
      "accountName": "Joe Car Hire",
      "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requesteeEmail": "sam@jrn-limited.com",
      "requestorEmail": "sam@jrn-limited.com",
      "requestType": "grantDocAccess",
      "requestedOnResource": "****",
      "requestedOnResourceName": "My Repo 1 - Lucy Gale",
      "status": "pending",
      "createdAt": "****",
      "updateHistory": []
    }
    """

    # Sam raises request to download above document again!!!
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId#last_created_docId'
    Then i should get response with status code 400 and data
    """
    {
      "message" : "Similar request already exists. Please cancel it to raise a new one."
    }
    """
    # kevin joins the account
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # Capture docId
    When i am logged in as sam@jrn-limited.com
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200

    # kevin (No Repo Access member) raises grantDocAccess Request
    When i am logged in as kevin@jrn-limited.com
    When i submit request of requestType: 'grantDocAccess', accountId: 'last_created_accountId', requestedOnResource: 'last_created_repoId#last_created_docId'
    Then i should get response with status code 403 and data
    """
    {
       "message": "Only owner and users having Repo Access Role can raise request of type grantDocAccess"
    }
    """

  Scenario: User's doc access request gets approved by a approver and downloads the doc
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

    # Sam uploads another file with correct repoId and docId
    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Rob Foster'
    Then i should get response with status code 200
    When i upload test-integration/files/Passport-01.jpg with 'saved_repoId' and 'saved_docId' and type 'passport'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Sam queries for downloadable documents
    When i am logged in as sam@jrn-limited.com
    When i query downloadable docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200 and data
    """
    [
      {
        "docId": "****",
        "repoId": "****",
        "accountId": "****",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com",
          "sam@jrn-limited.com"
        ],
        "downloadable": true,
        "docType": "drivingLicence",
        "text": null,
        "name": "Lucy Gale",
        "createdAt": "****",
        "errorMessage": null
      }
    ]
    """

    # Sam queries for all documents
    When i am logged in as sam@jrn-limited.com
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200 and data
    """
    [
      {
        "docId": "****",
        "repoId": "****",
        "accountId": "****",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com"
        ],
        "downloadable": false,
        "docType": "passport",
        "text": null,
        "name": "Rob Foster",
        "createdAt": "****",
        "errorMessage": null
      },
      {
        "docId": "****",
        "repoId": "****",
        "accountId": "****",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com",
          "sam@jrn-limited.com"
        ],
        "downloadable": true,
        "docType": "drivingLicence",
        "text": null,
        "name": "Lucy Gale",
        "createdAt": "****",
        "errorMessage": null
      }
    ]
    """

