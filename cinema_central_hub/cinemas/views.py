from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Film, Screentime, Theater, UserShowing
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
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

    # return render(request, 'homepage.html', {'films': films})
    return JsonResponse(films)


def movie_detail(request, film_slug):
    # Find the film by matching the slug in the booking_url
    # Use regex to match the exact slug pattern in the URL
    films = Film.objects.filter(
        booking_url__iregex=rf'/phim/{re.escape(film_slug)}/?$')

    if not films.exists():
        # Fallback: try broader search if exact match fails
        films = Film.objects.filter(booking_url__icontains=film_slug)

    film = get_object_or_404(films)

    # Get all screenings for this movie using the film slug directly
    screenings = Screentime.objects.filter(
        film_id=film_slug).order_by('date', 'time')

    # Parse custom date format and add proper date to each screening
    for screening in screenings:
        screening.proper_date = parse_custom_date(screening.date)

        # Check if user has added this screening to their list
        if request.user.is_authenticated:
            screening.is_saved = UserShowing.objects.filter(
                user=request.user,
                screening_id=screening.id
            ).exists()
        else:
            screening.is_saved = False

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
        'total_screenings': screenings.count(),
        'film_slug': film_slug
    }
    return JsonResponse(context)
    # return render(request, 'movie_detail.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            # messages.success(request, f'Account created for {username}! You can now log in.')
            # return redirect('login')
            return JsonResponse({'success': True, 'action': 'account created'})
        else:
            # messages.error(request, 'Please correct the errors below.')
            return JsonResponse({'success': False, 'error': 'invalid fields'})
    else:
        form = CustomUserCreationForm()
    return JsonResponse(form)
    # return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # next_url = request.GET.get('next', 'films')
                # return redirect(next_url)
                return JsonResponse({'success': True, 'action': 'login successfully'})
        else:
            # messages.error(request, 'Invalid username or password.')
            return JsonResponse({'success': True, 'error': 'Invalid username or password'})
    else:
        form = CustomAuthenticationForm()

    # return render(request, 'login.html', {'form': form})
    return JsonResponse(form)


def logout_view(request):
    logout(request)
    # messages.success(request, 'You have been logged out successfully.')
    return redirect('films')


@login_required
@require_POST
def add_to_my_shows(request):
    screening_id = request.POST.get('screening_id')
    film_slug = request.POST.get('film_slug')

    if not screening_id or not film_slug:
        return JsonResponse({'success': False, 'error': 'Missing data'})

    try:
        # Check if screening exists
        screening = get_object_or_404(Screentime, id=screening_id)

        # Create or get the UserShowing entry
        user_showing, created = UserShowing.objects.get_or_create(
            user=request.user,
            screening_id=int(screening_id),
            defaults={'film_slug': film_slug}
        )

        if created:
            return JsonResponse({'success': True, 'action': 'added'})
        else:
            return JsonResponse({'success': True, 'action': 'already_exists'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def remove_from_my_shows(request):
    screening_id = request.POST.get('screening_id')

    if not screening_id:
        return JsonResponse({'success': False, 'error': 'Missing screening ID'})

    try:
        user_showing = UserShowing.objects.get(
            user=request.user,
            screening_id=int(screening_id)
        )
        user_showing.delete()
        return JsonResponse({'success': True, 'action': 'removed'})

    except UserShowing.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Showing not found in your list'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def my_shows(request):
    # Get all user showings
    user_showings = UserShowing.objects.filter(
        user=request.user).order_by('-added_at')

    # Group by film
    films_data = {}
    for user_showing in user_showings:
        screening = user_showing.get_screening()
        if screening:
            film_slug = user_showing.film_slug

            if film_slug not in films_data:
                # Find the film
                try:
                    films = Film.objects.filter(
                        booking_url__icontains=film_slug)
                    if films.exists():
                        film = films.first()
                        films_data[film_slug] = {
                            'film': film,
                            'screenings': []
                        }
                except:
                    continue

            if film_slug in films_data:
                screening.proper_date = parse_custom_date(screening.date)
                screening.user_showing = user_showing

                # Get theater info
                try:
                    theater = Theater.objects.get(
                        theater_id=screening.cinema_id)
                    screening.theater_name = theater.name
                except Theater.DoesNotExist:
                    screening.theater_name = f"Theater {screening.cinema_id}"

                films_data[film_slug]['screenings'].append(screening)

    context = {
        'films_data': films_data,
        'total_showings': user_showings.count()
    }

    # return render(request, 'my_shows.html', context)
    return JsonResponse(context)
