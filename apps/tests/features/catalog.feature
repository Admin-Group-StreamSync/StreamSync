# tests/features/catalog.feature

Feature: Content catalog and search
  As a logged-in user
  I want to browse and search for movies and series
  So that I can find content I enjoy

  Background:
    Given a user "cat_user" with password "CatPass99!" exists
    And I am logged in as "cat_user" with password "CatPass99!"

  Scenario: Catalog loads successfully
    When I visit the catalog with mocked API
    Then the response status is 200

  Scenario: Catalog shows movies-only view
    When I visit the movies catalog with mocked API
    Then the response status is 200

  Scenario: Catalog shows series-only view
    When I visit the series catalog with mocked API
    Then the response status is 200

  Scenario: Catalog pagination limits to 12 items per page
    When I visit the catalog with 30 mock items
    Then the page contains at most 12 items

  Scenario: Catalog filters by platform
    When I visit the catalog filtered by platform "CinePlus"
    Then the response status is 200

  Scenario: Catalog filters by genre ID
    When I visit the catalog filtered by genre "1"
    Then the response status is 200

  Scenario: Catalog filters by director name
    When I visit the catalog filtered by director "nolan"
    Then the response status is 200

  Scenario: Catalog filters by minimum rating
    When I visit the catalog filtered by rating "8"
    Then the response status is 200

  Scenario: Fuzzy search finds a movie by exact title
    When I search for "Inception"
    Then the search result title is "Inception"

  Scenario: Fuzzy search finds a movie with a typo
    When I search for "Inceptoin"
    Then a search result is found

  Scenario: Empty search returns no result
    When I search for ""
    Then no search result is found

  Scenario: Content detail page loads for a movie
    Given a movie "8080_1" titled "Inception" exists in the database
    When I visit the detail page for movie "8080_1"
    Then the response status is 200

  Scenario: Content detail page returns 404 for unknown content
    When I visit the detail page for unknown movie "nonexistent_id"
    Then the response status is 404
