from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from reviews.igdb_service import IGDBService
from reviews.management.commands.populate_reviews import (
    Command as PopulateCommand
)
from reviews.models import Review, Genre
from developer.models import Developer
from publisher.models import Publisher
from django.contrib.auth.models import User
import datetime
import random
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generate reviews from IGDB games with random scores 5-10'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count', type=int, default=50,
            help='Number of reviews to generate (default 50)'
        )
        parser.add_argument(
            '--min-score', type=float, default=5.0,
            help='Minimum review score (default 5.0)'
        )
        parser.add_argument(
            '--max-score', type=float, default=10.0,
            help='Maximum review score (default 10.0)'
        )

    def handle(self, *args, **options):
        count = options['count']
        min_score = options['min_score']
        max_score = options['max_score']

        msg = f'Generating {count} reviews with scores {min_score}-{max_score}'
        self.stdout.write(self.style.NOTICE(msg))

        igdb = IGDBService()
        populate_helpers = PopulateCommand()
        
        # Popular game franchises
        games_list = [
            "Call of Duty", "FIFA", "Grand Theft Auto", "The Witcher",
            "Assassin's Creed", "Super Mario", "The Legend of Zelda",
            "Final Fantasy", "Resident Evil", "Halo", "God of War",
            "Minecraft", "Fortnite", "Red Dead Redemption", "Cyberpunk",
            "Apex Legends", "Overwatch", "Counter-Strike", "Valorant",
            "Destiny", "Battlefield", "Mass Effect", "Elder Scrolls",
            "Fallout", "Dark Souls", "Sekiro", "Bloodborne",
            "Monster Hunter", "Street Fighter", "Tekken", "Pokemon"
        ]

        created_count = 0
        attempts = 0
        max_attempts = count * 3

        with transaction.atomic():
            while created_count < count and attempts < max_attempts:
                attempts += 1
                
                search_term = random.choice(games_list)
                
                try:
                    games = igdb.search_games_with_platforms(
                        search_term, limit=10
                    )
                    
                    if not games:
                        continue
                    
                    game = random.choice(games)
                    title = game.get('name')
                    if not title:
                        continue
                    
                    slug = slugify(title)
                    
                    # Skip if exists
                    if (Review.objects.filter(title__iexact=title).exists() or
                            Review.objects.filter(slug=slug).exists()):
                        continue
                    
                    # Random score
                    review_score = round(
                        random.uniform(min_score, max_score), 1
                    )
                    
                    # Get developer and publisher
                    developer_obj = self.get_developer(game, populate_helpers)
                    publisher_obj = self.get_publisher(game, populate_helpers)
                    
                    if not (developer_obj and publisher_obj):
                        continue
                    
                    # Game details
                    description = (
                        game.get('summary', '') or f'Great game: {title}'
                    )
                    release_date = self.get_release_date(game)
                    featured_image = self.get_cover(game, title, populate_helpers)
                    review_text = self.get_review_text(title, populate_helpers)
                    reviewer = self.get_reviewer()
                    
                    # Create review
                    review = Review.objects.create(
                        title=title,
                        slug=slug,
                        publisher=publisher_obj,
                        developer=developer_obj,
                        description=description,
                        release_date=release_date,
                        review_score=review_score,
                        review_text=review_text,
                        reviewed_by=reviewer,
                        review_date=timezone.now(),
                        featured_image=featured_image,
                        is_featured=False,
                        is_published=True
                    )
                    
                    # Add genres
                    self.add_genres(game, review)
                    
                    created_count += 1
                    msg = (
                        f'Created {created_count}/{count}: '
                        f'{title} ({review_score}/10)'
                    )
                    self.stdout.write(self.style.SUCCESS(msg))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))
                    continue
        
        final_msg = f'Created {created_count} reviews'
        self.stdout.write(self.style.SUCCESS(final_msg))

    def get_developer(self, game, helpers):
        """Get or create developer"""
        if not game.get('developers'):
            return None
            
        dev = game['developers'][0]
        name = dev.get('name')
        if not name:
            return None
            
        logo_url = dev.get('logo_url', '')
        if logo_url and logo_url.startswith('//'):
            logo_url = 'https:' + logo_url
        
        cloud_logo = None
        if logo_url:
            try:
                cloud_logo = helpers.upload_developer_logo_to_cloudinary(
                    logo_url, name
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Logo upload failed: {e}')
                )
        
        obj, _ = Developer.objects.get_or_create(
            name=name,
            defaults={
                'description': dev.get('description', ''),
                'website': dev.get('website', ''),
                'founded_year': dev.get('founded_year') or None,
                'logo': cloud_logo or logo_url or ''
            }
        )
        return obj

    def get_publisher(self, game, helpers):
        """Get or create publisher"""
        if not game.get('publishers'):
            return None
            
        pub = game['publishers'][0]
        name = pub.get('name')
        if not name:
            return None
            
        logo_url = pub.get('logo_url', '')
        if logo_url and logo_url.startswith('//'):
            logo_url = 'https:' + logo_url
        
        cloud_logo = None
        if logo_url:
            try:
                cloud_logo = helpers.upload_publisher_logo_to_cloudinary(
                    logo_url, name
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Publisher logo upload failed: {e}')
                )
        
        obj, _ = Publisher.objects.get_or_create(
            name=name,
            defaults={
                'description': pub.get('description', ''),
                'website': pub.get('website', ''),
                'founded_year': pub.get('founded_year') or None,
                'logo': cloud_logo or logo_url or ''
            }
        )
        return obj

    def get_release_date(self, game):
        """Get release date"""
        release_date = datetime.date.today()
        if game.get('release_dates'):
            try:
                timestamp = game['release_dates'][0].get('date')
                if timestamp:
                    release_date = datetime.datetime.fromtimestamp(
                        timestamp
                    ).date()
            except Exception:
                pass
        return release_date

    def get_cover(self, game, title, helpers):
        """Get cover image"""
        cover_url = game.get('cover_url', '')
        if not cover_url and game.get('cover'):
            cover_url = game['cover'].get('url', '')
        
        if cover_url and cover_url.startswith('//'):
            cover_url = 'https:' + cover_url
        
        if cover_url:
            try:
                cloud_cover = helpers.upload_cover_to_cloudinary(
                    cover_url, title
                )
                if cloud_cover:
                    return cloud_cover
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Cover upload failed for {title}: {e}')
                )
        
        return 'placeholder'

    def get_review_text(self, title, helpers):
        """Generate review text"""
        # Skip AI generation for now due to rate limits
        return (
            f'<p>This is an auto-generated review for {title}.</p>'
            '<p>The game offers engaging gameplay mechanics and provides '
            'excellent entertainment value for players. With solid controls, '
            'immersive graphics, and compelling storyline, this title '
            'delivers a memorable gaming experience.</p>'
            '<p>Overall, this game represents a quality addition to any '
            'gaming library and is recommended for fans of the genre.</p>'
        )

    def get_reviewer(self):
        """Get reviewer"""
        reviewer = User.objects.order_by('?').first()
        if not reviewer:
            reviewer = User.objects.create_user(
                'reviewer', 'reviewer@example.com', 'password'
            )
        return reviewer

    def add_genres(self, game, review):
        """Add genres"""
        if game.get('genres'):
            for genre_data in game['genres']:
                genre_name = genre_data.get('name')
                if genre_name:
                    genre_obj, _ = Genre.objects.get_or_create(
                        name=genre_name
                    )
                    review.genres.add(genre_obj)