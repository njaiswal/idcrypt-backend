Feature: Add remove users as repo users

  Scenario Outline: Non-member users tries to submit join/leaveAsRepoApprover  | grant/removeRepoAccess request
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i am logged in as kevin@jrn-limited.com
    When i submit create account request with '{ "name": "Kevin Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type <requestType> for account 'Kevin Car Hire' and repo 'My Repo 1'

    Then i should get response with status code 403 and data
      """
      {
        "message" : "Only owner and members of account can raise request of type <requestType>"
      }
      """

    Examples:
      | requestType         |
      | joinAsRepoApprover  |
      | leaveAsRepoApprover |
      | grantRepoAccess     |
      | removeRepoAccess    |

  Scenario Outline: Member users tries to submit joinAsRepoApprover, granRepoAccess request
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
    And i submit request of type <requestType> for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "***",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          <approvers>
        ],
        "users": [
          <users>
        ],
        "createdAt": "***"
      }
    ]
    """
    Examples:
      | requestType        | approvers                                     | users                                        |
      | joinAsRepoApprover | "joe@jrn-limited.com",  "sam@jrn-limited.com" | "joe@jrn-limited.com"                        |
      | grantRepoAccess    | "joe@jrn-limited.com"                         | "joe@jrn-limited.com", "sam@jrn-limited.com" |

  Scenario Outline: Owner tries to submit joinAsRepoApprover, grantRepoAccess request for a member
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    And i GET "/accounts/"
    Then i should get response with status code 200

    And i submit request on behalf of 'sam@jrn-limited.com' of type <requestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 200 and data
      """
      {
        "requestId": "***",
        "accountId": "***",
        "accountName": "Joe Car Hire",
        "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
        "requestor": "30accff5-916d-47d7-bdbb-a3d7dc95feec",
        "requesteeEmail": "sam@jrn-limited.com",
        "requestorEmail": "joe@jrn-limited.com",
        "requestType": "<requestType>",
        "requestedOnResource": "***",
        "requestedOnResourceName": "My Repo 1",
        "status": "pending",
        "createdAt": "2020-03-02 15:59:33.414101",
        "updateHistory": []
      }
      """

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
      """
      [
        {
          "repoId": "***",
          "accountId": "***",
          "name": "My Repo 1",
          "desc": "My Repo 1",
          "retention": 30,
          "approvers": [
            <approvers>
          ],
          "users": [
            <users>
          ],
          "createdAt": "***"
        }
      ]
      """
    Examples:
      | requestType        | approvers                                     | users                                        |
      | joinAsRepoApprover | "joe@jrn-limited.com",  "sam@jrn-limited.com" | "joe@jrn-limited.com"                        |
      | grantRepoAccess    | "joe@jrn-limited.com"                         | "joe@jrn-limited.com", "sam@jrn-limited.com" |

  Scenario Outline: Owner tries to submit joinAsRepoApprover, grantRepoAccess request for a member twice
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    And i GET "/accounts/"
    Then i should get response with status code 200

    And i submit request on behalf of 'sam@jrn-limited.com' of type <requestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 200
    And i submit request on behalf of 'sam@jrn-limited.com' of type <requestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 400 and data
      """
      {
        "message": "Similar request already exists. Please cancel it to raise a new one."
      }
      """
    Examples:
      | requestType        |
      | joinAsRepoApprover |
      | grantRepoAccess    |

  Scenario Outline: Member users who is not already a approver|user tries to submit leaveAsRepoApprover|removeRepoAccess request
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
    And i GET "/accounts/"
    Then i should get response with status code 200
    And i submit request of type <requestType> for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 400 and data
      """
      {
        "message": "User does not have repository <role> role."
      }
      """
    Examples:
      | requestType         | role     |
      | leaveAsRepoApprover | approver |
      | removeRepoAccess    | user     |


  Scenario Outline: Approver himself tries to submit leaveAsRepoApprover|removeRepoAccess request
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
    And i GET "/accounts/"
    Then i should get response with status code 200
    And i submit request of type <joinRequestType> for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "***",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          <approversAfterJoining>
        ],
        "users": [
          <usersAfterJoining>
        ],
        "createdAt": "***"
      }
    ]
    """
    When i am logged in as sam@jrn-limited.com
    And i submit request of type <leaveRequestType> for account 'Joe Car Hire' and repo 'My Repo 1'
    Then i should get response with status code 200 and data
    """
    {
      "requestId": "***",
      "accountId": "***",
      "accountName": "Joe Car Hire",
      "requestee": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requestor": "86c8644c-d74e-495b-afe9-7eaff234bea9",
      "requesteeEmail": "sam@jrn-limited.com",
      "requestorEmail": "sam@jrn-limited.com",
      "requestType": "<leaveRequestType>",
      "requestedOnResource": "***",
      "requestedOnResourceName": "My Repo 1",
      "status": "pending",
      "createdAt": "***",
      "updateHistory": []
    }
    """
    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "a3ada0b7-5507-414e-9183-74d01e9d0e15",
        "accountId": "b93f3cf7-1fc8-43b9-a800-2730a3388ed2",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          <approversAfterLeaving>
        ],
        "users": [
          <usersAfterLeaving>
        ],
        "createdAt": "2020-03-02 18:15:15.978472"
      }
    ]
    """
    Examples:
      | joinRequestType    | leaveRequestType    | approversAfterJoining                        | usersAfterJoining                            | approversAfterLeaving | usersAfterLeaving     |
      | joinAsRepoApprover | leaveAsRepoApprover | "joe@jrn-limited.com", "sam@jrn-limited.com" | "joe@jrn-limited.com"                        | "joe@jrn-limited.com" | "joe@jrn-limited.com" |
      | grantRepoAccess    | removeRepoAccess    | "joe@jrn-limited.com"                        | "joe@jrn-limited.com", "sam@jrn-limited.com" | "joe@jrn-limited.com" | "joe@jrn-limited.com" |


  Scenario Outline: Owner tries to submit leaveAsRepoApprover|removeRepoAccess request for a member
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    When i am logged in as sam@jrn-limited.com
    And i submit request of type joinAccount for 'Joe Car Hire'

    When i am logged in as joe@jrn-limited.com
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'
    And i GET "/accounts/"
    Then i should get response with status code 200

    And i submit request on behalf of 'sam@jrn-limited.com' of type <joinRequestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 200
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "***",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          <approversAfterJoining>
        ],
        "users": [
          <usersAfterJoining>
        ],
        "createdAt": "***"
      }
    ]
    """

    And i submit request on behalf of 'sam@jrn-limited.com' of type <leaveRequestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 200
    And i mark last_submitted request as approved
    And i wait for last_submitted request to get 'closed'

    And i GET "/repos/"
    Then i should get response with status code 200 and data
    """
    [
      {
        "repoId": "***",
        "accountId": "***",
        "name": "My Repo 1",
        "desc": "My Repo 1",
        "retention": 30,
        "approvers": [
          <approversAfterLeaving>
        ],
        "users": [
          <usersAfterLeaving>
        ],
        "createdAt": "***"
      }
    ]
    """
    Examples:
      | joinRequestType    | leaveRequestType    | approversAfterJoining                        | usersAfterJoining                            | approversAfterLeaving | usersAfterLeaving     |
      | joinAsRepoApprover | leaveAsRepoApprover | "joe@jrn-limited.com", "sam@jrn-limited.com" | "joe@jrn-limited.com"                        | "joe@jrn-limited.com" | "joe@jrn-limited.com" |
      | grantRepoAccess    | removeRepoAccess    | "joe@jrn-limited.com"                        | "joe@jrn-limited.com", "sam@jrn-limited.com" | "joe@jrn-limited.com" | "joe@jrn-limited.com" |


  Scenario Outline: Owner tries to submit join/leaveAsRepoApprover | grant/removeRepoAccess request himself
    Given backend app is setup
    And i am logged in as joe@jrn-limited.com
    When i submit create account request with '{ "name": "Joe Car Hire", "repo": { "name": "My Repo 1",  "desc": "My Repo 1",  "retention": 30 }}'
    Then i should get response with status code 200

    And i submit request on behalf of 'joe@jrn-limited.com' of type <requestType> for accountName 'Joe Car Hire' and repoName 'My Repo 1'
    Then i should get response with status code 400 and data
    """
    {
      "message" : "<message>"
    }
    """
    Examples:
      | requestType         | message                                      |
      | joinAsRepoApprover  | Owner already has repository approver role.  |
      | leaveAsRepoApprover | Owner cannot leave repository approver role. |
      | grantRepoAccess     | Owner already has repository user role.      |
      | removeRepoAccess    | Owner cannot leave repository user role.     |

