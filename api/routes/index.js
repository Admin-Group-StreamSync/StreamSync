const express = require("express");
const router = express.Router();
const Repository = require("../repositories");
const db = require("../db");

const repository = new Repository(db);

router.get("/directors", async (req, res) => {
    return res.json(await repository.getAllDirectors());
});


router.get('/genres', async (req, res) => {
    return res.json(await repository.getAllGenres());
})

router.get('/age-ratings', async (req, res) => {
    return res.json(await repository.getAllAgeRatings());
})

router.get('/movies', async (req, res) => {

    if (Object.keys(req.query).length === 0) {
        return res.json(await repository.getAllMovies());
    }
    const filters = {
        genre: req.query.genre,
        director: req.query.director,
        age_rating: req.query.age_rating,
        id: req.query.id,
        title: req.query.title,
        synopsis: req.query.synopsis
    }
    return res.json(await repository.getAllMovies(filters));
})

router.get('/series', async (req, res) => {
    if (Object.keys(req.query).length === 0) {
        return res.json(await repository.getAllSeries());
    }
    const filters = {
        genre: req.query.genre,
        director: req.query.director,
        age_rating: req.query.age_rating,
        id: req.query.id,
        title: req.query.title,
        synopsis: req.query.synopsis
    }
    return res.json(await repository.getAllSeries(filters));
})

module.exports = router;