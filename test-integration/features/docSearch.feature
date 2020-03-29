Feature: User Uploads new doc

  Scenario Outline: GET docs/ api is called with various query parameters
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i GET "/docs/?<queryParam>"
    Then i get response with '<status_code>' and '<message>'

    Examples:
      | queryParam                    | status_code | message                                                                      |
      | accountId=xxxx                | 422         | { "errors": { "repoId": [ "Missing data for required field." ] }}            |
      | repoId=xxxx                   | 422         | { "errors": { "accountId": [ "Missing data for required field." ] }}         |
      | accountId=Abc-abc&repoId=xxxx | 422         | { "errors": { "accountId": [ "String does not match expected pattern." ] } } |
      | accountId=abc-abc&repoId=Xxxx | 422         | { "errors": { "repoId": [ "String does not match expected pattern." ] } }    |

  Scenario: User tries to search on account which the user is not a member of.
    # Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Sam tries to query docs
    When i am logged in as sam@jrn-limited.com
    And i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 403 and data
    """
    {
     "message": "Not Authorized."
    }
    """

  Scenario: User tries to search on repo which the user has no Repo Access Role
    # Joe create Account with default repo
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

    # Sam tries to query docs
    When i am logged in as sam@jrn-limited.com
    And i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 403 and data
    """
    {
     "message": "Only Account members having Repository Access Role have access to repository."
    }
    """

  Scenario: Owner search on repo with no documents
    # Joe create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Joe tries to query docs
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200 and data
    """
    []
    """

  Scenario: User can search docs by text
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

    # Sam uploads another file with correct repoId and docId
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Rob Foster'
    Then i should get response with status code 200
    When i upload test-integration/files/NID-01.png with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Sam searches for the uploaded doc without any text
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'null'
    Then i should get response with status code 200 and data
    """
    [
      {
        "docId": "***",
        "repoId": "***",
        "accountId": "***",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com"
        ],
        "downloadable": false,
        "docType": "drivingLicence",
        "text": null,
        "name": "Lucy Gale",
        "createdAt": "***",
        "errorMessage": null
      },
      {
        "docId": "***",
        "repoId": "***",
        "accountId": "***",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com"
        ],
        "downloadable": false,
        "docType": "drivingLicence",
        "text": null,
        "name": "Rob Foster",
        "createdAt": "***",
        "errorMessage": null
      }
    ]
    """

    # Sam searches for the uploaded doc with any text that matches name
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'Foster'
    Then i should get response with status code 200 and data
    """
    [
      {
        "docId": "***",
        "repoId": "***",
        "accountId": "***",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com"
        ],
        "downloadable": false,
        "docType": "drivingLicence",
        "text": null,
        "name": "Rob Foster",
        "createdAt": "***",
        "errorMessage": null
      }
    ]
    """

    # Sam searches for the uploaded doc with any text that matches document's extracted text
    When i query docs for account name 'Joe Car Hire' and repo name 'My Repo 1' and 'MORGAN'
    Then i should get response with status code 200 and data
    """
    [
      {
        "docId": "***",
        "repoId": "***",
        "accountId": "***",
        "retention": 30,
        "status": "indexed",
        "uploadedBy": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "uploadedByEmail": "sam@jrn-limited.com",
        "downloadableBy": [
          "joe@jrn-limited.com"
        ],
        "downloadable": false,
        "docType": "drivingLicence",
        "text": null,
        "name": "Lucy Gale",
        "createdAt": "***",
        "errorMessage": null
      }
    ]
    """

  Scenario: User uploads document with unknown docId
    # Joe Create Account with default repo
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    # Joe uploads a file with incorrect repoId, file is removed from uploads bucket and put in errors bucket
    When i upload test-integration/files/dl-01.jpg with 'incorrect' and 'incorrect' and type 'drivingLicence'
    Then last_uploaded_file is removed from upload bucket
    And last_uploaded_file appears in upload errors bucket
