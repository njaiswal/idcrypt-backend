Feature: This is just helper for dev work

  @devLocal
  Scenario: Add accounts for jrn, nishant and rashi
    Given backend app is setup
    And i am logged in as jrn@jrn-limited.com
    When i submit create account request with '{ "name": "JRN Main Account", "repo": { "name": "UK KYC",  "desc": "Customer kyc docs",  "retention": 30 }}'
    Then i should get response with status code 200

    # Add nishant to account
    When i am logged in as nishant@jrn-limited.com
    And i submit request of type joinAccount for 'JRN Main Account'

    When i am logged in as jrn@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as nishant@jrn-limited.com
    And i GET "/accounts/"
    Then i should get response with status code 200

    # Add joe to account
    When i am logged in as joe@jrn-limited.com
    And i submit request of type joinAccount for 'JRN Main Account'

    When i am logged in as jrn@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as joe@jrn-limited.com
    And i GET "/accounts/"
    Then i should get response with status code 200

    # Add kevin to account
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type joinAccount for 'JRN Main Account'

    When i am logged in as jrn@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    When i am logged in as kevin@jrn-limited.com
    And i GET "/accounts/"
    Then i should get response with status code 200

    When i am logged in as jrn@jrn-limited.com
    And i submit create repo request with '{ "name": "Germany KYC",  "desc": "German customer kyc docs",  "retention": 60 }'
    When i GET "/repos/"
    Then i should get response with status code 200

    # Kevin gets repo Access
    When i am logged in as kevin@jrn-limited.com
    And i submit request of type grantRepoAccess for account 'JRN Main Account' and repo 'UK KYC'
    When i am logged in as jrn@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    # kevin uploads a file with correct repoId and docId
    When i am logged in as kevin@jrn-limited.com
    And i submit create doc request with for account with name 'JRN Main Account' and repo with name 'UK KYC' and customer name 'Sarah Morgan'
    Then i should get response with status code 200
    When i upload test-integration/files/dl-01.jpg with 'saved_repoId' and 'saved_docId' and type 'drivingLicence'
    Then i wait for last_created doc to get 'indexed'
    And text for last_created doc is populated
    And last_uploaded_file is removed from upload bucket
