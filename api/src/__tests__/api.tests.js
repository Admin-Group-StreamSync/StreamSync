'use strict';

const request = require('supertest');

// Mock the pg Pool so tests run without a real DB
jest.mock('pg', () => {
  const mPool = {
    query: jest.fn(),
    end: jest.fn(),
  };
  return { Pool: jest.fn(() => mPool) };
});

const { Pool } = require('pg');
const pool = new Pool();

let app;

beforeAll(() => {
  // Provide a healthy DB mock before requiring the app
  pool.query.mockResolvedValue({ rows: [{ '?column?': 1 }] });
  app = require('../index');
});

afterEach(() => jest.clearAllMocks());

// Health
describe('GET /health', () => {
  it('returns 200 ok when DB is healthy', async () => {
    pool.query.mockResolvedValueOnce({ rows: [{ '?column?': 1 }] });
    const res = await request(app).get('/health');
    expect(res.statusCode).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  it('returns 500 when DB is unreachable', async () => {
    pool.query.mockRejectedValueOnce(new Error('connection refused'));
    const res = await request(app).get('/health');
    expect(res.statusCode).toBe(500);
  });
});

// Auth: register
describe('POST /auth/register', () => {
  it('returns 400 when fields are missing', async () => {
    const res = await request(app).post('/auth/register').send({ username: 'test' });
    expect(res.statusCode).toBe(400);
  });

  it('returns 201 on successful registration', async () => {
    pool.query.mockResolvedValueOnce({
      rows: [{ id: 1, username: 'john', email: 'john@test.com', role: 'consumer' }],
    });
    const res = await request(app)
      .post('/auth/register')
      .send({ username: 'john', email: 'john@test.com', password: 'Secret123!' });
    expect(res.statusCode).toBe(201);
    expect(res.body.role).toBe('consumer');
  });

  it('returns 409 on duplicate user', async () => {
    const err = new Error('duplicate');
    err.code = '23505';
    pool.query.mockRejectedValueOnce(err);
    const res = await request(app)
      .post('/auth/register')
      .send({ username: 'john', email: 'john@test.com', password: 'Secret123!' });
    expect(res.statusCode).toBe(409);
  });
});

// Auth: login
describe('POST /auth/login', () => {
  it('returns 401 when user not found', async () => {
    pool.query.mockResolvedValueOnce({ rows: [] });
    const res = await request(app)
      .post('/auth/login')
      .send({ email: 'nobody@test.com', password: 'pass' });
    expect(res.statusCode).toBe(401);
  });
});

//  Content: API-key guard
describe('GET /movies', () => {
  it('returns 401 without API key', async () => {
    const res = await request(app).get('/movies');
    expect(res.statusCode).toBe(401);
  });

  it('returns 403 with invalid API key', async () => {
    pool.query.mockResolvedValueOnce({ rows: [] }); // no key found
    const res = await request(app)
      .get('/movies')
      .set('X-API-KEY', 'bad-key');
    expect(res.statusCode).toBe(403);
  });
});

describe('GET /series', () => {
  it('returns 401 without API key', async () => {
    const res = await request(app).get('/series');
    expect(res.statusCode).toBe(401);
  });
});

// Protected routes: JWT guard
describe('GET /me/lists', () => {
  it('returns 401 without token', async () => {
    const res = await request(app).get('/me/lists');
    expect(res.statusCode).toBe(401);
  });
});

describe('GET /analytics/searches', () => {
  it('returns 401 without token', async () => {
    const res = await request(app).get('/analytics/searches');
    expect(res.statusCode).toBe(401);
  });
});

describe('GET /admin/users', () => {
  it('returns 401 without token', async () => {
    const res = await request(app).get('/admin/users');
    expect(res.statusCode).toBe(401);
  });
});