from django.db import models
from django.utils import timezone

class Film(models.Model):
    title = models.CharField(max_length=100, null=True)
    age_limit = models.CharField(max_length=100, null=True)
    movie_type = models.CharField(max_length=100, null=True)
    format = models.CharField(max_length=100, null=True)
    genre = models.CharField(max_length=100, null=True)
    image_url = models.TextField()
    booking_url = models.TextField()
    price = models.CharField(max_length=30)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        managed = False
        db_table = 'films'


class Screentime(models.Model):
    name = models.CharField(max_length=100)
    format = models.CharField(max_length=100)
    time = models.TimeField()
    date = models.DateTimeField()
    language = models.CharField(max_length=100)
    firstclass = models.CharField(max_length=10)
    cinema_id = models.CharField(max_length=30, null=True)
    film_id = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.date}"

    class Meta:
        managed = False
        db_table = 'screentimes'


class Theater(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=500)
    theater_id = models.CharField(max_length=30)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        managed = False
        db_table = 'cinemas'


class SeatData(models.Model):
    session_id = models.CharField(max_length=50)
    cinema_id = models.CharField(max_length=30)
    cinema_name = models.CharField(max_length=200)
    movie_title = models.CharField(max_length=200)
    movie_format = models.CharField(max_length=20)
    movie_language = models.CharField(max_length=50)
    movie_label = models.CharField(max_length=10)
    showtime = models.DateTimeField()
    screen_name = models.CharField(max_length=50)
    screen_number = models.IntegerField()
    seats_available = models.IntegerField()
    expire_time = models.DateTimeField()
    
    tickets_data = models.JSONField()
    seats_layout = models.JSONField()
    concession_items = models.JSONField()
    
    standard_price = models.DecimalField(max_digits=10, decimal_places=2)
    vip_price = models.DecimalField(max_digits=10, decimal_places=2)
    couple_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    search_date = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.movie_title} - {self.showtime}"

    class Meta:
        managed = False
        db_table = 'seat_data'
