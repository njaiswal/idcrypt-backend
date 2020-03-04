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
