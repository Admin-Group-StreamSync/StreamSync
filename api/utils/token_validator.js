const db = require('../db'); // tu conexión a la base de datos
const Repository = require("../repositories");
const repository = new Repository(db);

async function apiKeyMiddleware(req, res, next) {
    try {
        const apiKey = req.header('x-api-key');

        if (!apiKey) {
            return res.status(401).json({ error: 'API key required' });
        }

        const [rows] = await repository.checkApiKey(apiKey);

        if (rows.length === 0) {
            return res.status(403).json({ error: 'API invalid' });
        }

        // opcional: adjuntar info al request
        req.apiKey = rows[0];

        next();
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Error' });
    }
}

module.exports = apiKeyMiddleware;