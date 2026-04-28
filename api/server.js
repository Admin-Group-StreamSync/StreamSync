const express = require('express');
const swagger = require('swagger-ui-express');
const YAML = require('yamljs');
require('dotenv').config();
const apiKeyMiddleware = require('./utils/token_validator');
const indexRouter = require("./routes");

const swaggerDocument = YAML.load('./docs/swagger.yaml');

const app = express();

const PORT = process.env.PORT || 8080;

app.use('/docs', swagger.serve, swagger.setup(swaggerDocument));

app.use(apiKeyMiddleware);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

app.use("/", indexRouter);
