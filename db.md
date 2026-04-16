````mermaid
---
config:
  layout: elk
---
erDiagram
    direction TB

    COUNTRY {
        int id PK
        string name
        string iso_code
    }
    LANGUAGE {
        int id PK
        string name
        string iso_code
    }
    GENRE {
        int id PK
        string name
        string description
        datetime created_at
    }
    AGE_RATING {
        int id PK
        string description
        int minimum_age
    }
    DIRECTOR {
        int id PK
        string name
        date birth_date
        int country_id FK
        datetime created_at
    }
    MOVIE {
        int id PK
        string title
        text synopsis
        int year
        date release_date
        int duration_minutes
        float rating
        int genre_id FK
        int director_id FK
        int country_id FK
        int language_id FK
        int age_rating_id FK
        datetime created_at
    }
    SERIES {
        int id PK
        string title
        text synopsis
        int start_year
        int end_year
        int total_seasons
        float rating
        int genre_id FK
        int director_id FK
        int country_id FK
        int language_id FK
        int age_rating_id FK
        datetime created_at
    }
    PLATFORM {
        int id PK
        string name
        string slug
        string logo_url
        datetime created_at
    }
    CONTENT_AVAILABILITY {
        int id PK
        int movie_id FK
        int series_id FK
        int platform_id FK
        datetime available_from
        datetime available_until
    }
    USER {
        int id PK
        string username
        string email
        string password_hash
        string role
        datetime created_at
    }
    PLATFORM_ANALYST {
        int id PK
        int user_id FK
        int platform_id FK
        datetime created_at
    }
    WATCHLIST {
        int id PK
        int user_id FK
        string name
        datetime created_at
    }
    WATCHLIST_ITEM {
        int id PK
        int watchlist_id FK
        int movie_id FK
        int series_id FK
        int episode_number
        datetime time_progress
    }
    REVIEW {
        int id PK
        int user_id FK
        int movie_id FK
        int series_id FK
        int rating
        text comment
        datetime created_at
    }
    SEARCH_LOG {
        int id PK
        int user_id FK
        string query
        int platform_id FK
        datetime searched_at
    }
    API_KEY {
        int id PK
        string api_key
        boolean active
        datetime created_at
        datetime expires_at
    }

    COUNTRY ||--o{ DIRECTOR : nationality
    COUNTRY ||--o{ MOVIE : produces
    COUNTRY ||--o{ SERIES : produces
    LANGUAGE ||--o{ MOVIE : language
    LANGUAGE ||--o{ SERIES : language
    GENRE ||--o{ MOVIE : categorizes
    GENRE ||--o{ SERIES : categorizes
    AGE_RATING ||--o{ MOVIE : rates
    AGE_RATING ||--o{ SERIES : rates
    DIRECTOR ||--o{ MOVIE : directs
    DIRECTOR ||--o{ SERIES : directs
    PLATFORM ||--o{ CONTENT_AVAILABILITY : hosts
    MOVIE ||--o{ CONTENT_AVAILABILITY : available_on
    SERIES ||--o{ CONTENT_AVAILABILITY : available_on
    USER ||--o{ WATCHLIST : owns
    USER ||--o{ REVIEW : writes
    USER ||--o{ SEARCH_LOG : generates
    PLATFORM_ANALYST }o--|| USER : is
    PLATFORM_ANALYST }o--|| PLATFORM : analyzes
    WATCHLIST ||--o{ WATCHLIST_ITEM : contains
    MOVIE ||--o{ WATCHLIST_ITEM : in
    SERIES ||--o{ WATCHLIST_ITEM : in
    MOVIE ||--o{ REVIEW : receives
    SERIES ||--o{ REVIEW : receives
    PLATFORM ||--o{ SEARCH_LOG : scoped_to