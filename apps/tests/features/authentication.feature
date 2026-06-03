# tests/features/authentication.feature

Feature: Authentication flows
  As a user of StreamSync
  I want to be able to register, login, and manage my session
  So that I can access personalised content

  Background:
    Given the application is running

  Scenario: Successful user registration
    Given I am an anonymous user
    When I register with username "bdd_user" and password "SecurePass99!"
    Then a user account is created for "bdd_user"
    And the profile for "bdd_user" exists

  Scenario: Successful login displays a welcome message
    Given a user "login_user" with password "LoginPass99!" exists
    When I login as "login_user" with password "LoginPass99!"
    Then the login is successful

  Scenario: Login with wrong password fails
    Given a user "wrong_user" with password "CorrectPass99!" exists
    When I login as "wrong_user" with password "WrongPass!"
    Then the login page is shown again

  Scenario: Authenticated user can access the home page
    Given a user "home_user" with password "HomePass99!" exists
    And I am logged in as "home_user" with password "HomePass99!"
    When I visit the home page with mocked API
    Then the response status is 200

  Scenario: Password change requires authentication
    Given I am an anonymous user
    When I visit the password change page
    Then I am redirected to the login page

  Scenario: Password change with correct credentials succeeds
    Given a user "pwd_user" with password "OldPass123!" exists
    And I am logged in as "pwd_user" with password "OldPass123!"
    When I change my password from "OldPass123!" to "NewPass456!"
    Then I am redirected after password change
