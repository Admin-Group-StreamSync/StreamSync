const { Pool } = require("pg");

const pool = new Pool({
    user: process.env.DB_USER,
    host: process.env.DB_HOST,
    database: process.env.DB_NAME,
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT,
});


const db = {
    connect: () => pool.connect(),
    query: async (text, params) => {
        const client = await pool.connect();
        const result = await client.query(text, params);
        client.release();
        return result;
    },
    end: () => pool.end(),
};
module.exports = db;



