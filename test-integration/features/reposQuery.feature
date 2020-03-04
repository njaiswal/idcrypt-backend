Feature: As a user I want to query my repositories

  Scenario: New User has no repositories in the system
    Given backend app is setup
    When i am logged in as sam@jrn-limited.com
    And i GET "/repos/"
    Then i should get response with status code 404 and data
      """
      {
        "message": "User's Account not found"
      }
      """
