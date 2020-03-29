Feature: User Uploads new doc

  Scenario: User uploads a document
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

    # Sam uploads a file
    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Sarah Morgan'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Sam uploads another file but this time with unknown document type
    When i am logged in as sam@jrn-limited.com
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Sarah Morgan'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'someRandomType'
    Then i wait for last_created doc to get 'indexed'
    Then last_uploaded_file is removed from upload bucket
    And last_uploaded_file appears in upload errors bucket



  Scenario: User re-uploads document with already used docId
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
    And i submit create doc request with for account with name 'Joe Car Hire' and repo with name 'My Repo 1' and customer name 'Customer One'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'successfullyProcessed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket

    # Sam re-uploads a new file with same repoId and docId, file is rejected and moved to errors bucket
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then last_uploaded_file is removed from upload bucket
    And last_uploaded_file appears in upload errors bucket

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
