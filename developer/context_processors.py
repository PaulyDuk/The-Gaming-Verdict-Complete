from .models import Developer


def developers_context(request):
    # Only show developers that have associated games
    developers_with_games = [
        dev for dev in Developer.objects.all() if dev.games_count > 0
    ]
    return {'all_developers': developers_with_games}
