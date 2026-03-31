
--  Core schema + application users & auth
--  This file runs FIRST via docker-entrypoint-initdb.d ordering.


-- Reference tables

CREATE TABLE countries (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    iso_code VARCHAR(3)   NOT NULL UNIQUE
);

CREATE TABLE genres (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE directors (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(150) NOT NULL,
    birth_date DATE,
    country_id INTEGER REFERENCES countries(id),
    created_at DATE DEFAULT CURRENT_DATE
);

CREATE TABLE age_ratings (
    id          SERIAL PRIMARY KEY,
    description VARCHAR(50) NOT NULL,
    minimum_age INTEGER     NOT NULL
);

CREATE TABLE languages (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(50) NOT NULL,
    iso_code VARCHAR(3)  NOT NULL UNIQUE
);

-- Content tables

CREATE TABLE movies (
    id             SERIAL PRIMARY KEY,
    title          VARCHAR(255) UNIQUE NOT NULL,
    synopsis       TEXT,
    year           INTEGER     NOT NULL,
    release_date   DATE,
    duration_minutes INTEGER,
    rating         DECIMAL(3,1),
    genre_id       INTEGER REFERENCES genres(id)      NOT NULL,
    director_id    INTEGER REFERENCES directors(id)   NOT NULL,
    country_id     INTEGER REFERENCES countries(id)   NOT NULL,
    language_id    INTEGER REFERENCES languages(id)   NOT NULL,
    age_rating_id  INTEGER REFERENCES age_ratings(id) NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 year'
);

CREATE TABLE series (
    id             SERIAL PRIMARY KEY,
    title          VARCHAR(255) UNIQUE NOT NULL,
    synopsis       TEXT,
    start_year     INTEGER NOT NULL,
    end_year       INTEGER,
    total_seasons  INTEGER NOT NULL DEFAULT 1,
    rating         DECIMAL(3,1),
    genre_id       INTEGER REFERENCES genres(id)      NOT NULL,
    director_id    INTEGER REFERENCES directors(id)   NOT NULL,
    country_id     INTEGER REFERENCES countries(id)   NOT NULL,
    language_id    INTEGER REFERENCES languages(id)   NOT NULL,
    age_rating_id  INTEGER REFERENCES age_ratings(id) NOT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 year'
);

-- API Keys (platform integrations)

CREATE TABLE api_keys (
    id         SERIAL PRIMARY KEY,
    api_key    VARCHAR(64) NOT NULL UNIQUE,
    platform   VARCHAR(100),
    active     BOOLEAN   DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- User roles & authentication
-- Three roles:
--   consumer  – self-registered end users (lists, comments, ratings)
--   analyst   – platform analyst (read-only metrics; credentials set by admin)
--   admin     – superuser

CREATE TYPE user_role AS ENUM ('consumer', 'analyst', 'admin');

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(80)  NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          user_role    NOT NULL DEFAULT 'consumer',
    platform      VARCHAR(100),          -- for analysts: which platform they belong to
    active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- Consumer features: custom lists

CREATE TABLE user_lists (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name        VARCHAR(150) NOT NULL,
    description TEXT,
    is_public   BOOLEAN   DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_list_movies (
    list_id    INTEGER REFERENCES user_lists(id) ON DELETE CASCADE,
    movie_id   INTEGER REFERENCES movies(id)     ON DELETE CASCADE,
    added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, movie_id)
);

CREATE TABLE user_list_series (
    list_id    INTEGER REFERENCES user_lists(id) ON DELETE CASCADE,
    series_id  INTEGER REFERENCES series(id)     ON DELETE CASCADE,
    added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (list_id, series_id)
);

--  Consumer features: comments

CREATE TABLE comments (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    movie_id    INTEGER REFERENCES movies(id) ON DELETE CASCADE,
    series_id   INTEGER REFERENCES series(id) ON DELETE CASCADE,
    body        TEXT      NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT comment_target CHECK (
        (movie_id IS NOT NULL)::int + (series_id IS NOT NULL)::int = 1
    )
);

-- Consumer features: ratings

CREATE TABLE user_ratings (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER REFERENCES users(id)   ON DELETE CASCADE NOT NULL,
    movie_id   INTEGER REFERENCES movies(id)  ON DELETE CASCADE,
    series_id  INTEGER REFERENCES series(id)  ON DELETE CASCADE,
    score      DECIMAL(3,1) NOT NULL CHECK (score BETWEEN 0 AND 10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rating_target CHECK (
        (movie_id IS NOT NULL)::int + (series_id IS NOT NULL)::int = 1
    ),
    UNIQUE (user_id, movie_id),
    UNIQUE (user_id, series_id)
);

-- Analyst metrics: search & rating events

CREATE TABLE search_events (
    id          SERIAL  PRIMARY KEY,
    platform    VARCHAR(100) NOT NULL,
    query_text  TEXT,
    filters     JSONB,
    result_count INTEGER,
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes

CREATE INDEX idx_movies_genre      ON movies(genre_id);
CREATE INDEX idx_movies_director   ON movies(director_id);
CREATE INDEX idx_series_genre      ON series(genre_id);
CREATE INDEX idx_series_director   ON series(director_id);
CREATE INDEX idx_comments_movie    ON comments(movie_id);
CREATE INDEX idx_comments_series   ON comments(series_id);
CREATE INDEX idx_ratings_user      ON user_ratings(user_id);
CREATE INDEX idx_search_platform   ON search_events(platform);
CREATE INDEX idx_users_role        ON users(role);