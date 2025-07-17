from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.get_films, name='films'),
    path('movie/<str:film_slug>/', views.movie_detail, name='movie_detail'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('add-to-my-shows/', views.add_to_my_shows, name='add_to_my_shows'),
    path('remove-from-my-shows/', views.remove_from_my_shows, name='remove_from_my_shows'),
    path('my-shows/', views.my_shows, name='my_shows'),
]