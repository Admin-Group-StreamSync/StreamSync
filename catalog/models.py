from django.db import models


class Country(models.Model):
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = 'countries'

    def __str__(self):
        return self.name


class Language(models.Model):
    name = models.CharField(max_length=50)
    iso_code = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = 'languages'

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'genres'

    def __str__(self):
        return self.name


class AgeRating(models.Model):
    description = models.CharField(max_length=50)
    minimum_age = models.IntegerField()

    class Meta:
        db_table = 'age_ratings'

    def __str__(self):
        return self.description


class Director(models.Model):
    name = models.CharField(max_length=150)
    birth_date = models.DateField(blank=True, null=True)
    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'directors'

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    synopsis = models.TextField(blank=True, null=True)
    year = models.IntegerField()
    release_date = models.DateField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    age_rating = models.ForeignKey(AgeRating, on_delete=models.PROTECT)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'movies'

    def __str__(self):
        return f"{self.title} ({self.year})"


class Series(models.Model):
    title = models.CharField(max_length=255, unique=True)
    synopsis = models.TextField(blank=True, null=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    total_seasons = models.IntegerField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT)
    director = models.ForeignKey(Director, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    language = models.ForeignKey(Language, on_delete=models.PROTECT)
    age_rating = models.ForeignKey(AgeRating, on_delete=models.PROTECT)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'series'

    def __str__(self):
        return f"{self.title} ({self.start_year}-{self.end_year})"


class ApiKey(models.Model):
    api_key = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'api_keys'

    def is_expired(self):
        from django.utils import timezone
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    def __str__(self):
        return self.api_key[:8] + '...'