from django.contrib import admin
from .models import Film
from .admin_views import merge_films
# Register your models here.


@admin.register(Film)
class FilmAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "cgv_id",
        "rqg_film_id",
        "created_at",
    )
    list_filter = ("age_limit",)
    search_fields = ("title", "cgv_id", "rqg_film_id")
    actions = [merge_films]
