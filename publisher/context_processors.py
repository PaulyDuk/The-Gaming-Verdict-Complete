from .models import Publisher


def publishers_context(request):
    # Only show publishers that have associated games
    publishers_with_games = [
        pub for pub in Publisher.objects.all() if pub.games_count > 0
    ]
    return {'all_publishers': publishers_with_games}
