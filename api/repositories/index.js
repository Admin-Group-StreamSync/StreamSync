const db = require("../db");

class Repository {
    constructor(dbConnection) {
        this.db = dbConnection;
    }

    async checkApiKey(apiKey) {
        const result = await this.db.query("SELECT * FROM api_keys WHERE api_key = $1 AND active = true AND expires_at > current_timestamp", [apiKey]);
        return result.rows;
    }

    async getAllDirectors() {
        const result = await this.db.query("SELECT directors.id, directors.name, directors.birth_date, countries.name as country FROM directors LEFT JOIN countries ON directors.country_id = countries.id");
        return result.rows;
    }

    async getAllGenres() {
        const result = await this.db.query("SELECT id, name, description FROM genres");
        return result.rows;
    }

    async getAllAgeRatings() {
        const result = await this.db.query("SELECT id, description, minimum_age FROM age_ratings");
        return result.rows;
    }

    async getAllMovies(filters) {
        let query = "SELECT * FROM movies WHERE expires_at > current_timestamp";
        if (filters) {
            query += " AND ";
            const conditions = [];
            if (filters.genre) {
                conditions.push(`genre_id = ${filters.genre}`);
            }
            if (filters.director) {
                conditions.push(`director LIKE '%${filters.director}%'`);
            }
            if (filters.age_rating) {
                conditions.push(`age_rating_id = ${filters.age_rating}`);
            }
            if (filters.id) {
                conditions.push(`id = ${filters.id}`);
            }
            if (filters.title) {
                conditions.push(`title LIKE '%${filters.title}%'`);
            }
            if (filters.synopsis) {
                conditions.push(`synopsis LIKE '%${filters.synopsis}%'`);
            }
            query += conditions.join(" AND ");
        }
        console.log(query);
        const result = await this.db.query(query);
        return result.rows;
    }

    async getAllSeries(filters) {
        let query = "SELECT * FROM ser  ies WHERE expires_at > current_timestamp";
        if (filters) {
            query += " AND ";
            const conditions = [];
            if (filters.genre) {
                conditions.push(`genre_id = ${filters.genre}`);
            }
            if (filters.director) {
                conditions.push(`director LIKE '%${filters.director}%'`);
            }
            if (filters.age_rating) {
                conditions.push(`age_rating_id = ${filters.age_rating}`);
            }
            if (filters.id) {
                conditions.push(`id = ${filters.id}`);
            }
            if (filters.title) {
                conditions.push(`title LIKE '%${filters.title}%'`);
            }
            if (filters.synopsis) {
                conditions.push(`synopsis LIKE '%${filters.synopsis}%'`);
            }
            query += conditions.join(" AND ");
        }
        console.log(query);
        const result = await this.db.query(query);
        return result.rows;
    }
}

module.exports = Repository;