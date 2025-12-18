from .models import Genre


def genres_context(request):
    # Only show genres that have associated games
    genres_with_games = [
        genre for genre in Genre.objects.all() if genre.games_count > 0
    ]
    return {'genres': genres_with_games}
