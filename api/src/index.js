'use strict';

const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const app = express();
app.use(express.json());

// DB connection pool
const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'moviesdb',
  user:     process.env.DB_USER     || 'moviesuser',
  password: process.env.DB_PASSWORD || 'moviespassword',
});

const JWT_SECRET = process.env.JWT_SECRET || 'changeme';

//  Middleware: API Key auth (platform consumers)
async function requireApiKey(req, res, next) {
  const key = req.headers['x-api-key'];
  if (!key) return res.status(401).json({ error: 'Missing X-API-KEY header' });
  const { rows } = await pool.query(
    `SELECT id FROM api_keys WHERE api_key=$1 AND active=true AND (expires_at IS NULL OR expires_at > NOW())`,
    [key]
  );
  if (!rows.length) return res.status(403).json({ error: 'Invalid or expired API key' });
  next();
}

// Middleware: JWT auth
function requireJwt(roles = []) {
  return (req, res, next) => {
    const auth = req.headers.authorization;
    if (!auth?.startsWith('Bearer ')) return res.status(401).json({ error: 'Missing token' });
    try {
      const payload = jwt.verify(auth.slice(7), JWT_SECRET);
      if (roles.length && !roles.includes(payload.role))
        return res.status(403).json({ error: 'Insufficient permissions' });
      req.user = payload;
      next();
    } catch {
      res.status(401).json({ error: 'Invalid token' });
    }
  };
}

// Health check
app.get('/health', async (_req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok' });
  } catch {
    res.status(500).json({ status: 'db_error' });
  }
});

// Auth: register (consumer only)
app.post('/auth/register', async (req, res) => {
  const { username, email, password } = req.body;
  if (!username || !email || !password)
    return res.status(400).json({ error: 'username, email and password required' });
  try {
    const hash = await bcrypt.hash(password, 12);
    const { rows } = await pool.query(
      `INSERT INTO users (username, email, password_hash, role) VALUES ($1,$2,$3,'consumer') RETURNING id, username, email, role`,
      [username, email, hash]
    );
    res.status(201).json(rows[0]);
  } catch (e) {
    if (e.code === '23505') return res.status(409).json({ error: 'Username or email already exists' });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Auth: login (all roles)
app.post('/auth/login', async (req, res) => {
  const { email, password } = req.body;
  const { rows } = await pool.query(
    `SELECT id, username, email, password_hash, role, platform FROM users WHERE email=$1 AND active=true`,
    [email]
  );
  if (!rows.length) return res.status(401).json({ error: 'Invalid credentials' });
  const user = rows[0];
  const valid = await bcrypt.compare(password, user.password_hash);
  if (!valid) return res.status(401).json({ error: 'Invalid credentials' });
  const token = jwt.sign(
    { id: user.id, username: user.username, role: user.role, platform: user.platform },
    JWT_SECRET,
    { expiresIn: '8h' }
  );
  res.json({ token, role: user.role });
});

// Public / API-key protected content endpoints

app.get('/directors', requireApiKey, async (_req, res) => {
  const { rows } = await pool.query(`SELECT d.*, c.name AS country FROM directors d LEFT JOIN countries c ON c.id=d.country_id ORDER BY d.name`);
  res.json(rows);
});

app.get('/genres', requireApiKey, async (_req, res) => {
  const { rows } = await pool.query(`SELECT * FROM genres ORDER BY name`);
  res.json(rows);
});

app.get('/age-ratings', requireApiKey, async (_req, res) => {
  const { rows } = await pool.query(`SELECT * FROM age_ratings ORDER BY minimum_age`);
  res.json(rows);
});

app.get('/movies', requireApiKey, async (req, res) => {
  const { genre, director, age_rating, id, title, synopsis } = req.query;
  let q = `SELECT m.*, g.name AS genre, d.name AS director, ar.description AS age_rating
           FROM movies m
           LEFT JOIN genres g ON g.id=m.genre_id
           LEFT JOIN directors d ON d.id=m.director_id
           LEFT JOIN age_ratings ar ON ar.id=m.age_rating_id
           WHERE 1=1`;
  const params = [];
  if (id)         { params.push(id);         q += ` AND m.id=$${params.length}`; }
  if (title)      { params.push(`%${title}%`); q += ` AND m.title ILIKE $${params.length}`; }
  if (synopsis)   { params.push(`%${synopsis}%`); q += ` AND m.synopsis ILIKE $${params.length}`; }
  if (genre)      { params.push(genre);       q += ` AND g.name ILIKE $${params.length}`; }
  if (director)   { params.push(director);    q += ` AND d.name ILIKE $${params.length}`; }
  if (age_rating) { params.push(age_rating);  q += ` AND ar.description=$${params.length}`; }
  q += ' ORDER BY m.title';

  // Log search event for analytics
  pool.query(`INSERT INTO search_events (platform, query_text, filters) VALUES ('api',$1,$2)`,
    [title || null, JSON.stringify(req.query)]).catch(() => {});

  const { rows } = await pool.query(q, params);
  res.json(rows);
});

app.get('/series', requireApiKey, async (req, res) => {
  const { genre, director } = req.query;
  let q = `SELECT s.*, g.name AS genre, d.name AS director
           FROM series s
           LEFT JOIN genres g ON g.id=s.genre_id
           LEFT JOIN directors d ON d.id=s.director_id
           WHERE 1=1`;
  const params = [];
  if (genre)    { params.push(genre);    q += ` AND g.name ILIKE $${params.length}`; }
  if (director) { params.push(director); q += ` AND d.name ILIKE $${params.length}`; }
  q += ' ORDER BY s.title';
  const { rows } = await pool.query(q, params);
  res.json(rows);
});

// Consumer: lists
app.get('/me/lists', requireJwt(['consumer']), async (req, res) => {
  const { rows } = await pool.query(`SELECT * FROM user_lists WHERE user_id=$1`, [req.user.id]);
  res.json(rows);
});

app.post('/me/lists', requireJwt(['consumer']), async (req, res) => {
  const { name, description, is_public } = req.body;
  const { rows } = await pool.query(
    `INSERT INTO user_lists (user_id,name,description,is_public) VALUES ($1,$2,$3,$4) RETURNING *`,
    [req.user.id, name, description, is_public ?? false]
  );
  res.status(201).json(rows[0]);
});

// Consumer: comments
app.post('/comments', requireJwt(['consumer']), async (req, res) => {
  const { movie_id, series_id, body } = req.body;
  if (!body) return res.status(400).json({ error: 'body is required' });
  const { rows } = await pool.query(
    `INSERT INTO comments (user_id,movie_id,series_id,body) VALUES ($1,$2,$3,$4) RETURNING *`,
    [req.user.id, movie_id ?? null, series_id ?? null, body]
  );
  res.status(201).json(rows[0]);
});

// Consumer: ratings
app.post('/ratings', requireJwt(['consumer']), async (req, res) => {
  const { movie_id, series_id, score } = req.body;
  const { rows } = await pool.query(
    `INSERT INTO user_ratings (user_id,movie_id,series_id,score) VALUES ($1,$2,$3,$4)
     ON CONFLICT (user_id,movie_id) DO UPDATE SET score=EXCLUDED.score RETURNING *`,
    [req.user.id, movie_id ?? null, series_id ?? null, score]
  );
  res.status(201).json(rows[0]);
});

// Analyst: metrics
app.get('/analytics/searches', requireJwt(['analyst','admin']), async (req, res) => {
  const platform = req.user.platform || req.query.platform;
  const { rows } = await pool.query(
    `SELECT DATE_TRUNC('day', searched_at) AS day, COUNT(*) AS total
     FROM search_events WHERE ($1::text IS NULL OR platform=$1)
     GROUP BY day ORDER BY day DESC LIMIT 30`,
    [platform ?? null]
  );
  res.json(rows);
});

app.get('/analytics/ratings', requireJwt(['analyst','admin']), async (req, res) => {
  const { rows } = await pool.query(
    `SELECT 'movie' AS type, m.title, ROUND(AVG(r.score),2) AS avg_score, COUNT(*) AS votes
     FROM user_ratings r JOIN movies m ON m.id=r.movie_id GROUP BY m.title
     UNION ALL
     SELECT 'series', s.title, ROUND(AVG(r.score),2), COUNT(*)
     FROM user_ratings r JOIN series s ON s.id=r.series_id GROUP BY s.title
     ORDER BY avg_score DESC LIMIT 50`
  );
  res.json(rows);
});

// Admin: user management
app.get('/admin/users', requireJwt(['admin']), async (_req, res) => {
  const { rows } = await pool.query(`SELECT id,username,email,role,platform,active,created_at FROM users ORDER BY created_at DESC`);
  res.json(rows);
});

app.post('/admin/users', requireJwt(['admin']), async (req, res) => {
  const { username, email, password, role, platform } = req.body;
  const hash = await bcrypt.hash(password, 12);
  const { rows } = await pool.query(
    `INSERT INTO users (username,email,password_hash,role,platform) VALUES ($1,$2,$3,$4,$5) RETURNING id,username,email,role,platform`,
    [username, email, hash, role, platform ?? null]
  );
  res.status(201).json(rows[0]);
});

app.patch('/admin/users/:id', requireJwt(['admin']), async (req, res) => {
  const { active, role } = req.body;
  await pool.query(`UPDATE users SET active=$1, role=$2, updated_at=NOW() WHERE id=$3`, [active, role, req.params.id]);
  res.json({ updated: true });
});

// Start
const PORT = process.env.PORT || 8080;
app.listen(PORT, () => console.log(`API running on port ${PORT}`));
module.exports = app; // for tests