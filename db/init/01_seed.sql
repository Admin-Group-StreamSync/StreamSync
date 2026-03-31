-- ============================================================
--  01_seed.sql  – Reference data + sample content
-- ============================================================

-- Countries
INSERT INTO countries (name, iso_code) VALUES
('USA','USA'),('UK','UK'),('Spain','ESP'),('Mexico','MEX'),
('Argentina','ARG'),('Brazil','BRA'),('Canada','CAN'),('Australia','AUS'),
('Germany','DEU'),('France','FRA'),('Portugal','PRT'),('Denmark','DNK'),
('Italy','ITA'),('South Korea','KOR'),('Japan','JPN'),('China','CHN'),
('Russia','RUS'),('New Zealand','NZ'),('Chile','CHL');

-- Genres
INSERT INTO genres (name, description) VALUES
('Action','Action movies'),('Comedy','Comedy movies'),('Drama','Drama movies'),
('Horror','Horror movies'),('Sci-Fi','Sci-Fi movies'),('Fantasy','Fantasy movies'),
('Romance','Romance movies'),('Thriller','Thriller movies'),('Animation','Animation movies'),
('Documentary','Documentary movies'),('Mystery','Mystery movies'),('Adventure','Adventure movies'),
('Crime','Crime movies'),('Biography','Biography movies'),('History','History movies'),
('Music','Music movies'),('Musical','Musical movies'),('War','War movies'),
('Sport','Sport movies'),('Western','Western movies');

-- Languages
INSERT INTO languages (name, iso_code) VALUES
('English','EN'),('Spanish','ES'),('French','FR'),('German','DE'),
('Italian','IT'),('Portuguese','PT'),('Japanese','JA'),('Korean','KO'),
('Danish','DA'),('Chinese','ZH');

-- Age ratings
INSERT INTO age_ratings (description, minimum_age) VALUES
('G',0),('PG',13),('PG-13',13),('R',17),('NC-17',18),('PG-14',14),('Teen',13);

-- Directors
INSERT INTO directors (name, birth_date, country_id) VALUES
('Christopher Nolan','1970-07-30',(SELECT id FROM countries WHERE iso_code='UK')),
('Quentin Tarantino','1963-03-27',(SELECT id FROM countries WHERE iso_code='USA')),
('Steven Spielberg','1946-12-18',(SELECT id FROM countries WHERE iso_code='USA')),
('Martin Scorsese','1942-11-17',(SELECT id FROM countries WHERE iso_code='USA')),
('Pedro Almodóvar','1949-09-25',(SELECT id FROM countries WHERE iso_code='ESP')),
('Alejandro Amenábar','1972-03-31',(SELECT id FROM countries WHERE iso_code='ESP')),
('Fernando Trueba','1955-01-18',(SELECT id FROM countries WHERE iso_code='ESP')),
('Álex de la Iglesia','1965-12-04',(SELECT id FROM countries WHERE iso_code='ESP')),
('James Cameron','1954-08-16',(SELECT id FROM countries WHERE iso_code='CAN')),
('Ridley Scott','1937-11-30',(SELECT id FROM countries WHERE iso_code='UK')),
('Danny Boyle','1956-10-20',(SELECT id FROM countries WHERE iso_code='UK')),
('Guy Ritchie','1968-09-10',(SELECT id FROM countries WHERE iso_code='UK')),
('Ken Loach','1936-06-17',(SELECT id FROM countries WHERE iso_code='UK')),
('Steve McQueen','1969-10-09',(SELECT id FROM countries WHERE iso_code='UK')),
('Bong Joon-ho','1969-09-14',(SELECT id FROM countries WHERE iso_code='KOR')),
('Hayao Miyazaki','1941-01-05',(SELECT id FROM countries WHERE iso_code='JPN')),
('Luc Besson','1959-03-18',(SELECT id FROM countries WHERE iso_code='FRA')),
('Jacques Audiard','1952-04-30',(SELECT id FROM countries WHERE iso_code='FRA')),
('François Ozon','1967-11-15',(SELECT id FROM countries WHERE iso_code='FRA')),
('Wim Wenders','1945-08-14',(SELECT id FROM countries WHERE iso_code='DEU')),
('Fatih Akin','1973-08-25',(SELECT id FROM countries WHERE iso_code='DEU')),
('Tom Tykwer','1965-05-23',(SELECT id FROM countries WHERE iso_code='DEU')),
('Paolo Sorrentino','1970-05-31',(SELECT id FROM countries WHERE iso_code='ITA')),
('Pedro Costa','1959-11-04',(SELECT id FROM countries WHERE iso_code='PRT')),
('Thomas Vinterberg','1969-05-19',(SELECT id FROM countries WHERE iso_code='DNK')),
('Baz Luhrmann','1962-09-17',(SELECT id FROM countries WHERE iso_code='AUS')),
('Matt Reeves','1966-04-27',(SELECT id FROM countries WHERE iso_code='USA'));

-- API Keys (platform integrations)
INSERT INTO api_keys (api_key, platform, active, expires_at) VALUES
('b7c2e4f9a1d3c6e8f0a2b5d7c9e1f3a4','Platform-01',true, NOW() + INTERVAL '30 days'),
('d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9','Platform-02',true, NOW() + INTERVAL '30 days'),
('b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9','Platform-03',true, NOW() + INTERVAL '30 days');

-- Default admin user  (password: Admin1234! — bcrypt hash below)
INSERT INTO users (username, email, password_hash, role) VALUES
('admin','admin@moviesplatform.com','$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx','admin');

-- Sample movies (abbreviated — platform data loaded via API sync)
INSERT INTO movies (title, synopsis, year, release_date, duration_minutes, rating, genre_id, director_id, country_id, language_id, age_rating_id) VALUES
('Inception','A thief who steals corporate secrets through the use of dream-sharing technology.',2010,'2010-07-16',148,8.8,
 (SELECT id FROM genres WHERE name='Sci-Fi'),(SELECT id FROM directors WHERE name='Christopher Nolan'),
 (SELECT id FROM countries WHERE iso_code='USA'),(SELECT id FROM languages WHERE iso_code='EN'),(SELECT id FROM age_ratings WHERE description='PG-13')),
('Parasite','Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.',2019,'2019-05-30',132,8.5,
 (SELECT id FROM genres WHERE name='Drama'),(SELECT id FROM directors WHERE name='Bong Joon-ho'),
 (SELECT id FROM countries WHERE iso_code='KOR'),(SELECT id FROM languages WHERE iso_code='KO'),(SELECT id FROM age_ratings WHERE description='R')),
('Spirited Away','During her family''s move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits.',2001,'2002-09-20',125,8.6,
 (SELECT id FROM genres WHERE name='Animation'),(SELECT id FROM directors WHERE name='Hayao Miyazaki'),
 (SELECT id FROM countries WHERE iso_code='JPN'),(SELECT id FROM languages WHERE iso_code='JA'),(SELECT id FROM age_ratings WHERE description='PG'));

-- Sample series
INSERT INTO series (title, synopsis, start_year, end_year, total_seasons, rating, genre_id, director_id, country_id, language_id, age_rating_id) VALUES
('Stranger Things','A group of kids uncover supernatural mysteries in Hawkins, Indiana.',2016,2024,5,8.7,
 (SELECT id FROM genres WHERE name='Sci-Fi'),(SELECT id FROM directors WHERE name='Danny Boyle'),
 (SELECT id FROM countries WHERE iso_code='USA'),(SELECT id FROM languages WHERE iso_code='EN'),(SELECT id FROM age_ratings WHERE description='PG-13')),
('Squid Game','Hundreds of players compete in deadly versions of children''s games.',2021,2021,1,8.0,
 (SELECT id FROM genres WHERE name='Thriller'),(SELECT id FROM directors WHERE name='Bong Joon-ho'),
 (SELECT id FROM countries WHERE iso_code='KOR'),(SELECT id FROM languages WHERE iso_code='KO'),(SELECT id FROM age_ratings WHERE description='R'));