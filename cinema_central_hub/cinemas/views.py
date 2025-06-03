from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Film, Screentime, Theater
import re
from datetime import datetime

def extract_film_slug(booking_url):
    """Extract film slug from booking URL"""
    if booking_url:
        # Extract slug from URL like https://www.bhdstar.vn/phim/mission-impossible-nghiep-bao-cuoi-cung/
        match = re.search(r'/phim/([^/]+)/?', booking_url)
        if match:
            return match.group(1)
    return None

def parse_custom_date(date_str):
    """Parse custom date format YY-DD-MM to proper datetime
    Example: 2025-03-06 means June 3rd, 2025 (YY-DD-MM)
    """
    if isinstance(date_str, datetime):
        # If it's already a datetime object, extract components and reconstruct
        year = date_str.year
        day = date_str.month  # In the stored datetime, the day is actually in the month position
        month = date_str.day  # In the stored datetime, the month is actually in the day position
        return datetime(year, month, day)
        
    if date_str:
        try:
            # For string format: 2025-03-06 means June 3rd, 2025
            # First part (2025) is year
            # Second part (03) is day
            # Third part (06) is month
            parts = str(date_str).split('-')
            if len(parts) == 3:
                year = int(parts[0])    # 2025
                day = int(parts[1])     # 03 (3rd day)
                month = int(parts[2])   # 06 (June)
                return datetime(year, month, day)
        except (ValueError, IndexError) as e:
            print(f"Error parsing date {date_str}: {e}")
    return None

# Create your views here.
def get_films(request):

    # View for displaying list of movies with filtering and pagination
    films = Film.objects.all()
    
    # Add film slug to each film for URL generation
    for film in films:
        film.slug = extract_film_slug(film.booking_url)
    
    return render(request, 'homepage.html', {'films': films})

def movie_detail(request, film_slug):
    # Find the film by matching the slug in the booking_url
    # Use regex to match the exact slug pattern in the URL
    films = Film.objects.filter(booking_url__iregex=rf'/phim/{re.escape(film_slug)}/?$')
    
    if not films.exists():
        # Fallback: try broader search if exact match fails
        films = Film.objects.filter(booking_url__icontains=film_slug)
    
    film = get_object_or_404(films)
    
    # Get all screenings for this movie using the film slug directly
    screenings = Screentime.objects.filter(film_id=film_slug).order_by('date', 'time')
    
    # Parse custom date format and add proper date to each screening
    for screening in screenings:
        screening.proper_date = parse_custom_date(screening.date)
    
    # Group screenings by theater
    theaters = {}
    for screening in screenings:
        try:
            theater = Theater.objects.get(theater_id=screening.cinema_id)
            theater_name = theater.name
        except Theater.DoesNotExist:
            theater_name = f"Theater {screening.cinema_id}"
            
        if theater_name not in theaters:
            theaters[theater_name] = []
        theaters[theater_name].append(screening)
    
    context = {
        'film': film,
        'theaters': theaters,
        'total_screenings': screenings.count()
    }
    
    return render(request, 'movie_detail.html', context)
    