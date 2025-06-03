from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.get_films, name='films'),
    path('movie/<str:film_slug>/', views.movie_detail, name='movie_detail'),
]