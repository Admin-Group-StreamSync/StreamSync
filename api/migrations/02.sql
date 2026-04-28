-- 1. Tabla de países
CREATE TABLE countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    iso_code VARCHAR(3) NOT NULL UNIQUE
);

-- 2. Tabla de géneros
CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de directores
CREATE TABLE directors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    birth_date DATE,
    country_id INTEGER REFERENCES countries(id),
    -- just want day, month, year not hour
    created_at DATE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de ratings
CREATE TABLE age_ratings (
    id SERIAL PRIMARY KEY,
    description VARCHAR(50) NOT NULL,
    minimum_age INTEGER NOT NULL
);

-- 5. Tabla de idiomas
CREATE TABLE languages (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    iso_code VARCHAR(3) NOT NULL UNIQUE
);

-- 6. Tabla de películas
CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    synopsis TEXT,
    year INTEGER NOT NULL,
    release_date DATE,
    rating DECIMAL(3,1),
    genre_id INTEGER REFERENCES genres(id) NOT NULL,
    director_id INTEGER REFERENCES directors(id) NOT NULL,
    country_id INTEGER REFERENCES countries(id) NOT NULL,
    language_id INTEGER REFERENCES languages(id) NOT NULL,
    age_rating_id INTEGER REFERENCES age_ratings(id) NOT NULL,
    -- //without timestamp
    expires_at TIMESTAMP DEFAULT current_timestamp + INTERVAL '1 year'
);

-- 7. Tabla de series
CREATE TABLE series (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    synopsis TEXT,
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    total_seasons INTEGER NOT NULL,
    rating DECIMAL(3,1),
    genre_id INTEGER REFERENCES genres(id) NOT NULL,
    director_id INTEGER REFERENCES directors(id) NOT NULL,
    country_id INTEGER REFERENCES countries(id) NOT NULL,
    language_id INTEGER REFERENCES languages(id) NOT NULL,
    age_rating_id INTEGER REFERENCES age_ratings(id) NOT NULL,
    expires_at TIMESTAMP DEFAULT current_timestamp + INTERVAL '1 year'
);

-- 8. Tabla de claves API
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    api_key VARCHAR(64) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);


INSERT INTO api_keys (api_key, active, created_at, expires_at) VALUES
('c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8', true, NOW(), NOW() + INTERVAL '30 days'),
('d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9', true, NOW(), NOW() + INTERVAL '30 days'),
('e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0', true, NOW(), NOW() + INTERVAL '30 days'),
('f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1', true, NOW(), NOW() + INTERVAL '30 days'),
('a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2', true, NOW(), NOW() + INTERVAL '30 days'),
('b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3', true, NOW(), NOW() + INTERVAL '30 days'),
('c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4', true, NOW(), NOW() + INTERVAL '30 days'),
('d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5', true, NOW(), NOW() + INTERVAL '30 days'),
('e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6', true, NOW(), NOW() + INTERVAL '30 days'),
('f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7', true, NOW(), NOW() + INTERVAL '30 days');


INSERT INTO countries (name, iso_code) 
VALUES ('USA', 'USA'), ('UK', 'UK'), ('Spain', 'ESP'), ('Mexico', 'MEX'), 
('Argentina', 'ARG'), ('Brazil', 'BRA'), ('Canada', 'CAN'), ('Australia', 'AUS'), 
('Germany', 'DEU'), ('France', 'FRA'), ('Portugal', 'PRT'), ('Denmark', 'DNK'), ('Italy', 'ITA'), 
('South Korea', 'KOR'), ('Japan', 'JPN'), ('China', 'CHN'), ('Russia', 'RUS'), ('New Zealand', 'NZ'),
('Chile', 'CHL');

INSERT INTO genres (name, description) 
VALUES ('Action', 'Action movies'), ('Comedy', 'Comedy movies'), ('Drama', 'Drama movies'), 
('Horror', 'Horror movies'), ('Sci-Fi', 'Sci-Fi movies'), ('Fantasy', 'Fantasy movies'), 
('Romance', 'Romance movies'), ('Thriller', 'Thriller movies'), ('Animation', 'Animation movies'), 
('Documentary', 'Documentary movies'),
('Mystery', 'Mystery movies'),
('Adventure', 'Adventure movies'),
('Crime', 'Crime movies'),
('Biography', 'Biography movies'),
('History', 'History movies'),
('Music', 'Music movies'),
('Musical', 'Musical movies'),
('War', 'War movies'),
('Sport', 'Sport movies'),
('Western', 'Western movies');

INSERT INTO age_ratings (description, minimum_age) 
VALUES ('G', 0), ('PG', 13), ('PG-13', 13), ('R', 17), ('NC-17', 18),
('PG-14', 14),   -- común en algunos países
('Teen', 13),    -- alternativa para series
('Mature', 17);

INSERT INTO languages (name, iso_code) 
VALUES 
('English', 'EN'),
('Spanish', 'ES'),
('French', 'FR'),
('German', 'DE'),
('Italian', 'IT'),
('Japanese', 'JA'),
('Korean', 'KO'),
('Portuguese', 'PT'),
('Danish', 'DA'),
('Russian', 'RU'),
('Chinese', 'ZH');

--- directors
INSERT INTO directors (name, birth_date, country_id) VALUES
('Christopher Nolan', '1970-07-30', (SELECT id FROM countries WHERE iso_code='USA')),
('Quentin Tarantino', '1963-03-27', (SELECT id FROM countries WHERE iso_code='USA')),
('Pedro Almodóvar', '1949-09-25', (SELECT id FROM countries WHERE iso_code='ESP')),
('Bong Joon-ho', '1969-09-14', (SELECT id FROM countries WHERE iso_code='KOR')),
('Hayao Miyazaki', '1941-01-05', (SELECT id FROM countries WHERE iso_code='JPN')),
('Alejandro Amenábar', '1972-03-31', (SELECT id FROM countries WHERE iso_code='ESP')),
('Juan Antonio Bayona', '1975-05-09', (SELECT id FROM countries WHERE iso_code='ESP')),
('Fernando Trueba', '1955-01-18', (SELECT id FROM countries WHERE iso_code='ESP')),
('Álex de la Iglesia', '1965-12-04', (SELECT id FROM countries WHERE iso_code='ESP')),
('Isabel Coixet', '1960-04-09', (SELECT id FROM countries WHERE iso_code='ESP')),
('Carlos Saura', '1932-01-04', (SELECT id FROM countries WHERE iso_code='ESP')),
('Ken Loach', '1936-06-17', (SELECT id FROM countries WHERE iso_code='UK')),
('Danny Boyle', '1956-10-20', (SELECT id FROM countries WHERE iso_code='UK')),
('Guy Ritchie', '1968-09-10', (SELECT id FROM countries WHERE iso_code='UK')),
('Steve McQueen', '1969-10-09', (SELECT id FROM countries WHERE iso_code='UK')),
('Luc Besson', '1959-03-18', (SELECT id FROM countries WHERE iso_code='FRA')),
('Jean-Pierre Jeunet', '1953-09-03', (SELECT id FROM countries WHERE iso_code='FRA')),
('François Ozon', '1967-11-15', (SELECT id FROM countries WHERE iso_code='FRA')),
('Jacques Audiard', '1952-04-30', (SELECT id FROM countries WHERE iso_code='FRA')),
('Wim Wenders', '1945-08-14', (SELECT id FROM countries WHERE iso_code='DEU')),
('Werner Herzog', '1942-09-05', (SELECT id FROM countries WHERE iso_code='DEU')),
('Fatih Akin', '1973-08-25', (SELECT id FROM countries WHERE iso_code='DEU')),
('Tom Tykwer', '1965-05-23', (SELECT id FROM countries WHERE iso_code='DEU')),
('Paolo Sorrentino', '1970-05-31', (SELECT id FROM countries WHERE iso_code='ITA')),
('Federico Fellini', '1920-01-20', (SELECT id FROM countries WHERE iso_code='ITA')),
('Roberto Benigni', '1952-10-27', (SELECT id FROM countries WHERE iso_code='ITA')),
('Pedro Costa', '1959-12-29', (SELECT id FROM countries WHERE iso_code='PRT')),
('Lars von Trier', '1956-04-30', (SELECT id FROM countries WHERE iso_code='DNK')),
('Thomas Vinterberg', '1969-05-19', (SELECT id FROM countries WHERE iso_code='DNK')),
('Denis Villeneuve', '1967-10-03', (SELECT id FROM countries WHERE iso_code='CAN')),
('Wes Anderson', '1969-05-01', (SELECT id FROM countries WHERE iso_code='USA')),
('Jane Campion', '1954-04-30', (SELECT id FROM countries WHERE iso_code='NZ')),
('Byron Howard', '1968-12-09', (SELECT id FROM countries WHERE iso_code='USA')),
('Steven Spielberg', '1946-12-18', (SELECT id FROM countries WHERE iso_code='USA')),
('Jon Watts', '1981-06-28', (SELECT id FROM countries WHERE iso_code='USA')),
('Kenneth Branagh', '1960-12-10', (SELECT id FROM countries WHERE iso_code='UK')),
('Joel Coen', '1954-11-29', (SELECT id FROM countries WHERE iso_code='USA')),
('Guillermo del Toro', '1964-10-09', (SELECT id FROM countries WHERE iso_code='MEX')),
('Ridley Scott', '1937-11-30', (SELECT id FROM countries WHERE iso_code='UK')),
('Lana Wachowski', '1965-06-21', (SELECT id FROM countries WHERE iso_code='USA')),
('Aaron Sorkin', '1961-06-09', (SELECT id FROM countries WHERE iso_code='USA')),
('Pablo Larraín', '1976-08-19', (SELECT id FROM countries WHERE iso_code='CHL')),
('Joe Wright', '1972-08-25', (SELECT id FROM countries WHERE iso_code='UK')),
('Lin-Manuel Miranda', '1980-01-16', (SELECT id FROM countries WHERE iso_code='USA')),
('Domee Shi', '1989-09-14', (SELECT id FROM countries WHERE iso_code='CAN')),
('Angus MacLane', '1975-09-11', (SELECT id FROM countries WHERE iso_code='USA')),
('Colin Trevorrow', '1976-09-13', (SELECT id FROM countries WHERE iso_code='USA')),
('Joseph Kosinski', '1974-05-03', (SELECT id FROM countries WHERE iso_code='USA')),
('Sam Raimi', '1959-10-23', (SELECT id FROM countries WHERE iso_code='USA')),
('Dan Kwan', '1989-07-10', (SELECT id FROM countries WHERE iso_code='USA')), 
('Matt Reeves', '1966-04-27', (SELECT id FROM countries WHERE iso_code='USA')),
('Baz Luhrmann', '1962-09-17', (SELECT id FROM countries WHERE iso_code='AUS')), 
('James Cameron', '1954-08-16', (SELECT id FROM countries WHERE iso_code='CAN'));

INSERT INTO movies (title, year, director_id, country_id, genre_id, rating, age_rating_id, language_id) VALUES
('Once Upon a Time in Hollywood', 2019, (SELECT id FROM directors WHERE name='Quentin Tarantino'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM genres WHERE name='Comedy'), 7.6, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('The Hateful Eight', 2015, (SELECT id FROM directors WHERE name='Quentin Tarantino'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM genres WHERE name='Western'), 7.8, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('Volver', 2006, (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Drama'), 7.6, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('The Skin I Live In', 2011, (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Thriller'), 7.6, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='ES')),
('Pain and Glory', 2019, (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Drama'), 7.6, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('Parasite', 2019, (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM genres WHERE name='Thriller'), 8.6, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='KO')),
('Memories of Murder', 2003, (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM genres WHERE name='Crime'), 8.1, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='KO')),
('The Host', 2006, (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM genres WHERE name='Horror'), 7.1, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='KO')),
('Spirited Away', 2001, (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM genres WHERE name='Animation'), 8.6, (SELECT id FROM age_ratings WHERE description='G'), (SELECT id FROM languages WHERE iso_code='JA')),
('Princess Mononoke', 1997, (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM genres WHERE name='Fantasy'), 8.4, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='JA')),
('My Neighbor Totoro', 1988, (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM genres WHERE name='Animation'), 8.2, (SELECT id FROM age_ratings WHERE description='G'), (SELECT id FROM languages WHERE iso_code='JA')),
('The Others', 2001, (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Horror'), 7.6, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('Belle Époque', 1992, (SELECT id FROM directors WHERE name='Fernando Trueba'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Romance'), 7.5, (SELECT id FROM age_ratings WHERE description='PG'), (SELECT id FROM languages WHERE iso_code='ES')),
('The Day of the Beast', 1995, (SELECT id FROM directors WHERE name='Álex de la Iglesia'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Horror'), 7.7, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='ES')),
('The Oxford Murders', 2008, (SELECT id FROM directors WHERE name='Álex de la Iglesia'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Mystery'), 6.9, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('The Secret Life of Words', 2005, (SELECT id FROM directors WHERE name='Isabel Coixet'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Drama'), 7.3, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('Elegy', 2008, (SELECT id FROM directors WHERE name='Isabel Coixet'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Romance'), 6.7, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='ES')),
('Cría Cuervos', 1976, (SELECT id FROM directors WHERE name='Carlos Saura'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM genres WHERE name='Drama'), 7.7, (SELECT id FROM age_ratings WHERE description='PG'), (SELECT id FROM languages WHERE iso_code='ES')),
('Land and Freedom', 1995, (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 7.7, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='EN')),
('I, Daniel Blake', 2016, (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 7.9, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='EN')),
('Trainspotting', 1996, (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 8.1, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('Slumdog Millionaire', 2008, (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 8.0, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='EN')),
('Snatch', 2000, (SELECT id FROM directors WHERE name='Guy Ritchie'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Crime'), 8.0, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('Sherlock Holmes', 2009, (SELECT id FROM directors WHERE name='Guy Ritchie'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Action'), 7.6, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='EN')),
('Hunger', 2008, (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 7.8, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('12 Years a Slave', 2013, (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM genres WHERE name='Drama'), 8.1, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='EN')),
('Léon: The Professional', 1994, (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Action'), 8.5, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='FR')),
('Lucy', 2014, (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Sci-Fi'), 6.4, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='FR')),
('Amélie', 2001, (SELECT id FROM directors WHERE name='Jean-Pierre Jeunet'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Romance'), 8.3, (SELECT id FROM age_ratings WHERE description='PG'), (SELECT id FROM languages WHERE iso_code='FR')),
('Delicatessen', 1991, (SELECT id FROM directors WHERE name='Jean-Pierre Jeunet'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Comedy'), 8.0, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='FR')),
('8 Women', 2002, (SELECT id FROM directors WHERE name='François Ozon'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Musical'), 7.3, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='FR')),
('A Prophet', 2009, (SELECT id FROM directors WHERE name='Jacques Audiard'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM genres WHERE name='Crime'), 8.5, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='FR')),
('Paris, Texas', 1984, (SELECT id FROM directors WHERE name='Wim Wenders'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Drama'), 8.5, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='DE')),
('Wings of Desire', 1987, (SELECT id FROM directors WHERE name='Wim Wenders'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Drama'), 8.5, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='DE')),
('Fitzcarraldo', 1982, (SELECT id FROM directors WHERE name='Werner Herzog'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Adventure'), 7.7, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='DE')),
('Nosferatu the Vampyre', 1979, (SELECT id FROM directors WHERE name='Werner Herzog'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Horror'), 7.7, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='DE')),
('Head-On', 2004, (SELECT id FROM directors WHERE name='Fatih Akin'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Drama'), 7.5, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='DE')),
('Run Lola Run', 1998, (SELECT id FROM directors WHERE name='Tom Tykwer'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM genres WHERE name='Thriller'), 7.7, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='DE')),
('The Great Beauty', 2013, (SELECT id FROM directors WHERE name='Paolo Sorrentino'), (SELECT id FROM countries WHERE iso_code='ITA'), (SELECT id FROM genres WHERE name='Drama'), 7.8, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='IT')),
('Youth', 2015, (SELECT id FROM directors WHERE name='Paolo Sorrentino'), (SELECT id FROM countries WHERE iso_code='ITA'), (SELECT id FROM genres WHERE name='Drama'), 7.3, (SELECT id FROM age_ratings WHERE description='PG-13'), (SELECT id FROM languages WHERE iso_code='IT')),
('La Dolce Vita', 1960, (SELECT id FROM directors WHERE name='Federico Fellini'), (SELECT id FROM countries WHERE iso_code='ITA'), (SELECT id FROM genres WHERE name='Drama'), 8.0, (SELECT id FROM age_ratings WHERE description='PG'), (SELECT id FROM languages WHERE iso_code='IT')),
('The Hunt', 2012, (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM genres WHERE name='Drama'), 8.3, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='DA')),
('Another Round', 2020, (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM genres WHERE name='Comedy'), 7.8, (SELECT id FROM age_ratings WHERE description='R'), (SELECT id FROM languages WHERE iso_code='DA'));

INSERT INTO movies (title, synopsis, year, release_date, rating, genre_id, director_id, country_id, language_id, age_rating_id, expires_at) VALUES
('The French Dispatch', 'Stories from the final issue of an American magazine in a fictional French city.', 2021, '2021-10-22', 7.2, (SELECT id FROM genres WHERE name='Comedy'), (SELECT id FROM directors WHERE name='Wes Anderson'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('The Power of the Dog', 'A rancher intimidates everyone around him in 1920s Montana.', 2021, '2021-11-17', 6.9, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Jane Campion'), (SELECT id FROM countries WHERE iso_code='NZ'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '15 days'),
('Encanto', 'A magical family lives in a wondrous house in Colombia.', 2021, '2021-11-24', 7.3, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Byron Howard'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('West Side Story', 'Two young lovers are caught in the rivalry of New York street gangs.', 2021, '2021-12-10', 7.6, (SELECT id FROM genres WHERE name='Romance'), (SELECT id FROM directors WHERE name='Steven Spielberg'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '12 days'),
('Spider-Man: No Way Home', 'Peter Parker faces multiverse villains while dealing with his identity.', 2021, '2021-12-17', 8.3, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Jon Watts'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Belfast', 'A young boy grows up during the Troubles in Northern Ireland.', 2021, '2021-11-12', 7.3, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Kenneth Branagh'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '25 days'),
('The Tragedy of Macbeth', 'Macbeth receives a prophecy and descends into murder and madness.', 2021, '2021-12-25', 7.2, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Joel Coen'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Spencer', 'Princess Diana struggles with her role in the royal family.', 2021, '2021-11-05', 6.6, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Pablo Larraín'), (SELECT id FROM countries WHERE iso_code='CHL'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '20 days'),
('The Last Duel', 'A knight accuses his friend of raping his wife in medieval France.', 2021, '2021-10-15', 7.4, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Ridley Scott'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Cyrano', 'A poetic man helps his friend woo the woman he loves.', 2021, '2021-12-31', 6.7, (SELECT id FROM genres WHERE name='Romance'), (SELECT id FROM directors WHERE name='Joe Wright'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '21 days'),
('Tick, Tick… Boom!', 'A songwriter in New York struggles to make it big before 30.', 2021, '2021-11-12', 7.5, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Lin-Manuel Miranda'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Encanto 2', 'The magical Madrigal family faces new challenges.', 2023, '2023-11-24', 7.2, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Byron Howard'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG'), NOW() + INTERVAL '30 days'),
('Turning Red', 'A teenage girl transforms into a giant red panda when stressed.', 2022, '2022-03-11', 7.0, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Domee Shi'), (SELECT id FROM countries WHERE iso_code='CAN'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('Everything Everywhere All At Once', 'A woman explores infinite universes and her choices.', 2022, '2022-03-11', 8.1, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Dan Kwan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '24 days'),
('The Batman', 'Batman faces corruption in Gotham while confronting the Riddler.', 2022, '2022-03-04', 7.9, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Matt Reeves'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Elvis', 'The life story of Elvis Presley and his rise to fame.', 2022, '2022-06-24', 7.2, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Baz Luhrmann'), (SELECT id FROM countries WHERE iso_code='AUS'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '16 days'),
('Avatar: The Way of Water', 'Jake Sully and Neytiri face a new threat on Pandora.', 2022, '2022-12-16', 7.8, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='James Cameron'), (SELECT id FROM countries WHERE iso_code='CAN'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT);



INSERT INTO series (title, synopsis, start_year, end_year, total_seasons, rating, genre_id, director_id, country_id, language_id, age_rating_id, expires_at) VALUES
('Westworld', 'An amusement park populated by androids experiences a violent rebellion.', 2016, 2022, 4, 8.6, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Christopher Nolan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Breaking Bad', 'A chemistry teacher turns to making methamphetamine after a terminal diagnosis.', 2008, 2013, 5, 9.5, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Better Call Saul', 'The trials of a small-time lawyer in the criminal underworld.', 2015, 2022, 6, 8.7, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Quentin Tarantino'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Queen s Gambit', 'A young orphan becomes a chess prodigy.', 2020, 2020, 1, 8.6, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Fernando Trueba'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '35 days'),
('House of Cards', 'A ruthless politician manipulates his way to the presidency.', 2013, 2018, 6, 8.7, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Christopher Nolan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Crown', 'Chronicles the reign of Queen Elizabeth II.', 2016, 2023, 6, 8.6, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '22 days'),
('Fargo', 'Different crimes in the same town inspire a darkly comedic anthology.', 2014, 2020, 4, 8.9, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('True Detective', 'Detectives hunt serial killers over multiple timelines.', 2014, 2019, 3, 9.0, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Pedro Costa'), (SELECT id FROM countries WHERE iso_code='PRT'), (SELECT id FROM languages WHERE iso_code='PT'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '12 days'),
('Lupin', 'A gentleman thief inspired by Arsène Lupin seeks revenge.', 2021, 2023, 2, 7.8, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Vikings', 'The exploits of legendary Viking chieftains and their families.', 2013, 2020, 6, 8.5, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Jean-Pierre Jeunet'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '14 days'),
('Rome', 'The fall of the Roman Republic through the eyes of soldiers and politicians.', 2005, 2007, 2, 8.7, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='François Ozon'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Shadow and Bone', 'A young soldier discovers magical powers that could unite her war-torn world.', 2021, 2023, 2, 7.9, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '37 days'),
('The Last Kingdom', 'The story of a Saxon nobleman in 9th century England.', 2015, 2022, 5, 8.4, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '29 days'),
('Mindhunter', 'FBI agents interview serial killers to solve ongoing cases.', 2017, 2019, 2, 8.6, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Black Mirror', 'Standalone episodes exploring the dark side of technology.', 2011, 2019, 5, 8.8, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Ozark', 'A financial planner moves his family to the Ozarks to launder money.', 2017, 2022, 4, 8.4, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Christopher Nolan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '21 days'),
('The Boys', 'A group of vigilantes fight corrupt superheroes.', 2019, 2023, 3, 8.7, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Quentin Tarantino'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Expanse', 'A conspiracy threatens peace between Earth, Mars, and the Asteroid Belt.', 2015, 2022, 6, 8.5, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM languages WHERE iso_code='KO'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Narcos', 'The rise and fall of Pablo Escobar and the Medellín cartel.', 2015, 2017, 3, 8.8, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '12 days'),
('Narcos: Mexico', 'The origins of the modern drug war in Mexico.', 2018, 2021, 3, 8.4, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Peaky Blinders', 'A gangster family epic set in 1919 Birmingham.', 2013, 2022, 6, 8.8, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '27 days'),
('The Wire', 'The drug scene in Baltimore is explored through the eyes of both law enforcers and drug dealers.', 2002, 2008, 5, 9.3, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Christopher Nolan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('House of the Dragon', 'The Targaryen civil war in Westeros.', 2022, 2024, 2, 8.5, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Costa'), (SELECT id FROM countries WHERE iso_code='PRT'), (SELECT id FROM languages WHERE iso_code='PT'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '9 days'),
('Squid Game', 'Hundreds of players compete in deadly versions of children’s games.', 2021, 2021, 1, 8.0, (SELECT id FROM genres WHERE name='Thriller'), (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM languages WHERE iso_code='KO'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '14 days'),
('Severance', 'Employees undergo a procedure to separate work memories from personal memories.', 2022, 2023, 2, 8.7, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Christopher Nolan'), (SELECT id FROM countries WHERE iso_code='USA'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Morning Show', 'The drama behind the scenes of a morning news program.', 2019, 2023, 3, 8.0, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '11 days'),
('Bridgerton', 'The romantic and scandalous lives of the Bridgerton family in Regency-era London.', 2020, 2023, 3, 7.3, (SELECT id FROM genres WHERE name='Romance'), (SELECT id FROM directors WHERE name='Fernando Trueba'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Love, Death & Robots', 'Animated short stories exploring futuristic worlds and dark humor.', 2019, 2022, 3, 8.5, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '25 days'),
('The Haunting of Hill House', 'Family confronts ghosts from their past after living in a haunted mansion.', 2018, 2020, 2, 8.6, (SELECT id FROM genres WHERE name='Horror'), (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Haunting of Bly Manor', 'A governess takes care of two children in a mysterious manor.', 2020, 2020, 1, 7.4, (SELECT id FROM genres WHERE name='Horror'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '20 days'),
('Foundation', 'A mathematician predicts the fall of the Galactic Empire and creates a plan to save humanity.', 2021, 2023, 2, 7.3, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Bong Joon-ho'), (SELECT id FROM countries WHERE iso_code='KOR'), (SELECT id FROM languages WHERE iso_code='KO'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('The Wheel of Time', 'Moiraine leads a group of five young people in a world of magic and prophecy.', 2021, 2023, 2, 7.2, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Costa'), (SELECT id FROM countries WHERE iso_code='PRT'), (SELECT id FROM languages WHERE iso_code='PT'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '28 days'),
('Shadowhunters', 'A young girl discovers she is part of a race of human-angel hybrids called Shadowhunters.', 2016, 2019, 3, 6.6, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('The 100', 'Teenagers are sent to Earth after a nuclear apocalypse to see if the planet is habitable.', 2014, 2020, 7, 7.6, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '15 days'),
('Sense8', 'Eight strangers discover they are mentally and emotionally linked.', 2015, 2018, 2, 8.3, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Fernando Trueba'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('The OA', 'A missing blind woman returns after seven years with mysterious powers.', 2016, 2019, 2, 7.8, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '10 days'),
('Chilling Adventures of Sabrina', 'Teen witch navigates darkness and magical powers in the mortal and spirit worlds.', 2018, 2020, 4, 7.5, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Alejandro Amenábar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Castlevania', 'A vampire hunter fights Dracula and his dark forces.', 2017, 2021, 4, 8.2, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Midnight Gospel', 'A spacecaster travels to surreal worlds interviewing beings about life and death.', 2020, 2020, 1, 8.2, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='PG'), NOW() + INTERVAL '12 days'),
('Adventure Time', 'A boy and his magical dog explore the Land of Ooo.', 2010, 2018, 10, 8.6, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('The Owl House', 'A teenager discovers a magical world and becomes a witch.', 2020, 2023, 3, 8.0, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='PG'), NOW() + INTERVAL '21 days'),
('The Legend of Korra', 'A young avatar learns to balance the four elements.', 2012, 2014, 4, 8.4, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('Avatar: The Last Airbender', 'A boy must master all four elements to save the world.', 2005, 2008, 3, 9.2, (SELECT id FROM genres WHERE name='Animation'), (SELECT id FROM directors WHERE name='Hayao Miyazaki'), (SELECT id FROM countries WHERE iso_code='JPN'), (SELECT id FROM languages WHERE iso_code='JA'), (SELECT id FROM age_ratings WHERE description='PG'), NOW() + INTERVAL '18 days'),
('She-Ra and the Princesses of Power', 'A rebellion princess discovers her destiny and unites magical kingdoms.', 2018, 2020, 5, 7.4, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('Elite', 'Teenagers at an elite private school navigate romance, murder, and class conflict.', 2018, 2023, 6, 7.5, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Pedro Almodóvar'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('La Casa de Papel: Berlin', 'Spin-off focusing on Berlin, the mastermind behind heists.', 2023, 2023, 1, 7.8, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Álex de la Iglesia'), (SELECT id FROM countries WHERE iso_code='ESP'), (SELECT id FROM languages WHERE iso_code='ES'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '12 days'),
('Ragnarok', 'Teenagers discover they are reincarnations of Norse gods.', 2020, 2023, 3, 7.3, (SELECT id FROM genres WHERE name='Fantasy'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Gomorrah', 'The inner workings of the Neapolitan mafia and family dynamics.', 2014, 2021, 5, 8.7, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Paolo Sorrentino'), (SELECT id FROM countries WHERE iso_code='ITA'), (SELECT id FROM languages WHERE iso_code='IT'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '18 days'),
('Suburra: Blood on Rome', 'Corruption and crime in Rome politics and streets.', 2017, 2020, 3, 7.5, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Paolo Sorrentino'), (SELECT id FROM countries WHERE iso_code='ITA'), (SELECT id FROM languages WHERE iso_code='IT'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Babylon Berlin', 'Crime and political intrigue in 1920s Berlin.', 2017, 2023, 4, 8.4, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Wim Wenders'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM languages WHERE iso_code='DE'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '15 days'),
('4 Blocks', 'A Lebanese family in Berlin struggles to control its criminal empire.', 2017, 2019, 3, 8.3, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Fatih Akin'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM languages WHERE iso_code='DE'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Young Wallander', 'A young detective solves crimes in modern Sweden.', 2020, 2022, 2, 6.8, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Tom Tykwer'), (SELECT id FROM countries WHERE iso_code='DEU'), (SELECT id FROM languages WHERE iso_code='DE'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '22 days'),
('Call My Agent!', 'Agents in Paris manage celebrity clients and chaotic personal lives.', 2015, 2020, 4, 8.5, (SELECT id FROM genres WHERE name='Comedy'), (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Marseille', 'The mayoral politics and corruption in Marseille, France.', 2016, 2018, 2, 6.6, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Jacques Audiard'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '13 days'),
('Lupin: Part 3', 'Arsène Lupin continues his masterful heists across France.', 2023, 2023, 1, 7.9, (SELECT id FROM genres WHERE name='Action'), (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Borgen', 'The political and personal struggles of the Danish Prime Minister.', 2010, 2022, 3, 8.4, (SELECT id FROM genres WHERE name='Drama'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '16 days'),
('The Rain', 'A virus carried by rainfall wipes out much of Scandinavia.', 2018, 2020, 3, 6.5, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Occupied', 'Political thriller where Norway is occupied by Russia.', 2015, 2020, 3, 7.7, (SELECT id FROM genres WHERE name='Thriller'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '19 days'),
('Beforeigners', 'People from the past appear in modern Norway.', 2019, 2021, 2, 6.9, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Rita', 'A rebellious schoolteacher navigates her students and personal life.', 2012, 2020, 5, 8.3, (SELECT id FROM genres WHERE name='Comedy'), (SELECT id FROM directors WHERE name='Thomas Vinterberg'), (SELECT id FROM countries WHERE iso_code='DNK'), (SELECT id FROM languages WHERE iso_code='DA'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '14 days'),
('Balthazar', 'French crime series following a brilliant detective and his team.', 2018, 2023, 5, 7.7, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Jacques Audiard'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Call My Agent!: Spin-Off', 'A new batch of celebrity agents navigates Parisian showbiz.', 2023, 2023, 1, 7.6, (SELECT id FROM genres WHERE name='Comedy'), (SELECT id FROM directors WHERE name='Luc Besson'), (SELECT id FROM countries WHERE iso_code='FRA'), (SELECT id FROM languages WHERE iso_code='FR'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '20 days'),
('Baptiste', 'Detective Julien Baptiste investigates cases across Europe.', 2019, 2022, 3, 7.9, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('The Capture', 'A British surveillance officer uncovers deep conspiracies.', 2019, 2022, 3, 7.5, (SELECT id FROM genres WHERE name='Thriller'), (SELECT id FROM directors WHERE name='Guy Ritchie'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '17 days'),
('Bodyguard', 'A war veteran becomes the bodyguard of a controversial politician.', 2018, 2018, 1, 8.1, (SELECT id FROM genres WHERE name='Thriller'), (SELECT id FROM directors WHERE name='Guy Ritchie'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), DEFAULT),
('Marcella', 'A detective returns to work while struggling with her personal demons.', 2016, 2020, 3, 7.4, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='R'), NOW() + INTERVAL '15 days'),
('Grantchester', 'A vicar and a detective solve crimes in the 1950s English countryside.', 2014, 2023, 9, 8.2, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Ken Loach'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), DEFAULT),
('Sherlock', 'Modern-day Sherlock Holmes solves crimes in London.', 2010, 2017, 4, 9.1, (SELECT id FROM genres WHERE name='Crime'), (SELECT id FROM directors WHERE name='Steve McQueen'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '18 days'),
('Doctor Who', 'A time-traveling alien saves civilizations throughout time.', 2005, 2023, 13, 8.6, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG'), DEFAULT),
('Torchwood', 'A secret organization investigates extraterrestrial threats in Cardiff.', 2006, 2011, 4, 7.9, (SELECT id FROM genres WHERE name='Sci-Fi'), (SELECT id FROM directors WHERE name='Danny Boyle'), (SELECT id FROM countries WHERE iso_code='UK'), (SELECT id FROM languages WHERE iso_code='EN'), (SELECT id FROM age_ratings WHERE description='PG-13'), NOW() + INTERVAL '21 days');