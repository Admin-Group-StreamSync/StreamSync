# tests/features/lists_and_reviews.feature

Feature: Lists and reviews management
  As a logged-in user
  I want to manage my watchlists and write reviews
  So that I can organise and share my opinions

  Background:
    Given a user "lr_user" with password "LRPass99!" exists
    And I am logged in as "lr_user" with password "LRPass99!"
    And a movie "8080_1" titled "Inception" exists in the database

  Scenario: Add content to a list
    Given I have a folder named "Favourites"
    When I add movie "8080_1" to my list with folder
    Then movie "8080_1" is in my list

  Scenario: Adding the same content twice is idempotent
    Given I have a folder named "WatchLater"
    When I add movie "8080_1" to my list with folder
    And I add movie "8080_1" to my list with folder
    Then there is only 1 item for movie "8080_1" in my list

  Scenario: Remove content from a list
    Given movie "8080_1" is in my personal list
    When I remove movie "8080_1" from my list
    Then movie "8080_1" is not in my list

  Scenario: Write a new review
    When I post a review for movie "8080_1" with score 8 and comment "Amazing!"
    Then a review exists for movie "8080_1" with score 8

  Scenario: Update an existing review
    Given I have already reviewed movie "8080_1" with score 5
    When I post a review for movie "8080_1" with score 9 and comment "Changed my mind"
    Then a review exists for movie "8080_1" with score 9

  Scenario: Review score is replaced not duplicated
    Given I have already reviewed movie "8080_1" with score 5
    When I post a review for movie "8080_1" with score 7 and comment "Better"
    Then there is only 1 review for movie "8080_1"

  Scenario: Anonymous user cannot add to list
    Given I am logged out
    When I try to add movie "8080_1" to my list
    Then I am redirected to the login page

  Scenario: Anonymous user cannot write a review
    Given I am logged out
    When I post a review for movie "8080_1" with score 8 and comment "Test"
    Then I am redirected to the login page

  Scenario: Lists page loads for authenticated user
    When I visit the lists page
    Then the response status is 200
