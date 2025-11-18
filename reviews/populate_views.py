from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.urls import reverse
from .igdb_service import IGDBService
from .models import Review, Genre
from developer.models import Developer
from publisher.models import Publisher
from .management.commands.populate_reviews import Command as PopulateCommand
import json
import datetime


def is_superuser(user):
    return user.is_superuser


def get_paginated_redirect(current_page):
    """Helper function to create redirect URL with pagination"""
    redirect_url = reverse('reviews:populate_interface')
    if current_page and str(current_page) != '1':
        redirect_url += f'?page={current_page}'
    return redirect_url


@user_passes_test(is_superuser)
def populate_reviews_interface(request):
    """Main interface for populating reviews"""

    # Handle bulk actions on existing reviews
    if request.method == 'POST':
        action = request.POST.get('action')
        existing_review_ids = request.POST.getlist('existing_review_ids')
        current_page = request.POST.get(
            'current_page', request.GET.get('page', 1))

        if action == 'delete_selected':
            if existing_review_ids:
                try:
                    deleted_reviews = Review.objects.filter(
                        id__in=existing_review_ids)
                    count = deleted_reviews.count()
                    deleted_reviews.delete()
                    messages.success(
                        request, f'Successfully deleted {count} review(s)')
                except Exception as e:
                    messages.error(
                        request, f'Error deleting reviews: {str(e)}')
            else:
                messages.warning(request, 'No reviews selected for deletion')
            return redirect(get_paginated_redirect(current_page))

        elif action == 'publish_selected':
            if existing_review_ids:
                try:
                    count = Review.objects.filter(
                        id__in=existing_review_ids).update(is_published=True)
                    messages.success(
                        request, f'Successfully published {count} review(s)')
                except Exception as e:
                    messages.error(
                        request, f'Error publishing reviews: {str(e)}')
            else:
                messages.warning(request, 'No reviews selected')
            return redirect(get_paginated_redirect(current_page))

        elif action == 'unpublish_selected':
            if existing_review_ids:
                try:
                    count = Review.objects.filter(
                        id__in=existing_review_ids).update(is_published=False)
                    messages.success(
                        request, f'Successfully unpublished {count} review(s)')
                except Exception as e:
                    messages.error(
                        request, f'Error unpublishing reviews: {str(e)}')
            else:
                messages.warning(request, 'No reviews selected')
            return redirect(get_paginated_redirect(current_page))

        elif action == 'feature_selected':
            if existing_review_ids:
                try:
                    count = Review.objects.filter(
                        id__in=existing_review_ids).update(is_featured=True)
                    messages.success(
                        request, f'Successfully featured {count} review(s)')
                except Exception as e:
                    messages.error(
                        request, f'Error featuring reviews: {str(e)}')
            else:
                messages.warning(request, 'No reviews selected')
            return redirect(get_paginated_redirect(current_page))

        elif action == 'unfeature_selected':
            if existing_review_ids:
                try:
                    count = Review.objects.filter(
                        id__in=existing_review_ids).update(is_featured=False)
                    messages.success(
                        request, f'Successfully unfeatured {count} review(s)')
                except Exception as e:
                    messages.error(
                        request, f'Error unfeaturing reviews: {str(e)}')
            else:
                messages.warning(request, 'No reviews selected')
            return redirect(get_paginated_redirect(current_page))

    # Handle single review deletion (legacy support)
    if request.method == 'POST' and 'delete_review' in request.POST:
        review_id = request.POST.get('review_id')
        current_page = request.POST.get(
            'current_page', request.GET.get('page', 1))
        try:
            review = Review.objects.get(id=review_id)
            title = review.title
            review.delete()
            messages.success(request, f'Successfully deleted review: {title}')
        except Review.DoesNotExist:
            messages.error(request, 'Review not found')
        except Exception as e:
            messages.error(request, f'Error deleting review: {str(e)}')
        return redirect(get_paginated_redirect(current_page))

    if request.method == 'POST':
        search_term = request.POST.get('search', '')
        limit = int(request.POST.get('limit', 50))

        # Get games from IGDB
        igdb_service = IGDBService()
        if search_term:
            games = igdb_service.search_games_with_platforms(
                search_term, limit=limit)
        else:
            games = igdb_service.search_games_with_platforms('', limit=limit)

        # Format games for template
        formatted_games = []
        for idx, game in enumerate(games, 1):
            title = game.get('name', 'Unknown')
            slug = slugify(title)

            # Check if review already exists
            existing_review = Review.objects.filter(
                Q(title__iexact=title) | Q(slug=slug)
            ).first()

            year = None
            if 'release_dates' in game and game['release_dates']:
                try:
                    timestamp = game['release_dates'][0]['date']
                    year = datetime.datetime.fromtimestamp(timestamp).year
                except Exception:
                    year = 'Unknown'
            platforms = ', '.join([
                p.get('name', 'Unknown') for p in game.get('platforms', [])
            ])

            review_url = (reverse('reviews:review_detail',
                                  args=[existing_review.slug])
                          if existing_review else None)

            formatted_games.append({
                'index': idx,
                'title': title,
                'year': year,
                'platforms': platforms,
                'summary': game.get('summary', ''),
                'has_review': existing_review is not None,
                'review_url': review_url,
                # Store as JSON string for hidden input
                'raw_data': json.dumps(game)
            })

        # Get existing reviews
        existing_reviews_queryset = Review.objects.all().order_by(
            '-created_on')

        # Count featured reviews
        featured_count = existing_reviews_queryset.filter(
            is_featured=True).count()

        # Add pagination for existing reviews
        paginator = Paginator(existing_reviews_queryset, 50)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'reviews/populate_reviews.html', {
            'games': formatted_games,
            'search_term': search_term,
            'limit': limit,
            'existing_reviews': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'page_obj': page_obj,
            'paginator': paginator,
            'featured_count': featured_count,
        })

    # Get existing reviews for GET request
    existing_reviews = Review.objects.all().order_by('-created_on')

    # Count featured reviews
    featured_count = existing_reviews.filter(is_featured=True).count()

    # Add pagination for existing reviews
    paginator = Paginator(existing_reviews, 50)  # Show 50 reviews per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reviews/populate_reviews.html', {
        'existing_reviews': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'paginator': paginator,
        'featured_count': featured_count,
    })


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def create_reviews_from_selection(request):
    """Create reviews from selected games"""
    try:
        selected_games_data = request.POST.getlist('selected_games')
        review_scores = request.POST.getlist('review_scores')

        if not selected_games_data:
            messages.error(request, 'No games selected')
            return redirect('reviews:populate_interface')

        created_reviews = 0
        skipped_reviews = 0
        populate_command = PopulateCommand()

        with transaction.atomic():
            for i, game_json in enumerate(selected_games_data):
                try:
                    game = json.loads(game_json)
                    if i < len(review_scores):
                        score_str = review_scores[i]
                        if not score_str.strip():
                            # silently skip if no score entered
                            continue
                        try:
                            review_score = float(score_str)
                        except ValueError:
                            # silently skip if invalid score
                            continue
                    else:
                        review_score = 5.0

                    # Get published and featured status for this game
                    is_published_key = f'is_published_{i}'
                    is_featured_key = f'is_featured_{i}'

                    # HTML checkboxes only send data when checked
                    is_published = is_published_key in request.POST
                    is_featured = is_featured_key in request.POST

                    title = game.get('name')
                    slug = slugify(title)

                    # Check if review already exists
                    existing_review = Review.objects.filter(
                        Q(title__iexact=title) | Q(slug=slug)
                    ).first()

                    if existing_review:
                        skipped_reviews += 1
                        continue

                    description = game.get('summary', '')
                    release_date = None
                    if 'release_dates' in game and game['release_dates']:
                        try:
                            timestamp = game['release_dates'][0]['date']
                            release_date = datetime.datetime.fromtimestamp(
                                timestamp).date()
                        except Exception:
                            release_date = None

                    # Handle developer
                    developer_obj = None
                    if game.get('developers'):
                        dev_data = game['developers'][0]
                        logo_url = dev_data.get('logo_url', '')
                        if logo_url and logo_url.startswith('//'):
                            logo_url = 'https:' + logo_url
                        cloudinary_logo_id = (
                            populate_command
                            .upload_developer_logo_to_cloudinary(
                                logo_url, dev_data['name']
                            )
                        )
                        developer_obj, _ = Developer.objects.get_or_create(
                            name=dev_data['name'],
                            defaults={
                                'description': dev_data.get('description', ''),
                                'website': dev_data.get('website', ''),
                                'founded_year': (
                                    dev_data.get('founded_year') or None
                                ),
                                'logo': (
                                    cloudinary_logo_id if cloudinary_logo_id
                                    else logo_url
                                )
                            }
                        )

                    # Handle publisher
                    publisher_obj = None
                    if game.get('publishers'):
                        pub_data = game['publishers'][0]
                        logo_url = pub_data.get('logo_url', '')
                        if logo_url and logo_url.startswith('//'):
                            logo_url = 'https:' + logo_url
                        cloudinary_logo_id = (
                            populate_command
                            .upload_publisher_logo_to_cloudinary(
                                logo_url, pub_data['name']
                            )
                        )
                        publisher_obj, _ = Publisher.objects.get_or_create(
                            name=pub_data['name'],
                            defaults={
                                'description': pub_data.get('description', ''),
                                'website': pub_data.get('website', ''),
                                'founded_year': (
                                    pub_data.get('founded_year') or None
                                ),
                                'logo': (
                                    cloudinary_logo_id if cloudinary_logo_id
                                    else logo_url
                                )
                            }
                        )

                    # Create review if both developer and publisher exist
                    if developer_obj and publisher_obj:
                        user = User.objects.order_by('?').first()

                        # Generate AI review
                        ai_review_text = populate_command.generate_ai_review(
                            title)
                        if ai_review_text:
                            review_text = ai_review_text
                        else:
                            review_text = f"Auto-generated review for {title}."
                        review_date = datetime.datetime.now()

                        # Download and upload cover image
                        cover_url = game.get('cover_url', '')
                        if cover_url.startswith('//'):
                            cover_url = 'https:' + cover_url
                        cloudinary_id = (
                            populate_command.upload_cover_to_cloudinary(
                                cover_url, title
                            )
                        )
                        featured_image = (
                            cloudinary_id if cloudinary_id else 'placeholder'
                        )

                        review, created = Review.objects.get_or_create(
                            title=title,
                            slug=slug,
                            defaults={
                                'publisher': publisher_obj,
                                'developer': developer_obj,
                                'description': description,
                                'release_date': (
                                    release_date or datetime.date.today()
                                ),
                                'review_score': review_score,
                                'review_text': review_text,
                                'reviewed_by': user,
                                'review_date': review_date,
                                'featured_image': featured_image,
                                'is_featured': is_featured,
                                'is_published': is_published
                            }
                        )

                        # Add genres to review
                        genre_objs = []
                        for genre in game.get('genres', []):
                            genre_name = genre.get('name')
                            if genre_name:
                                genre_obj, _ = Genre.objects.get_or_create(
                                    name=genre_name
                                )
                                genre_objs.append(genre_obj)
                        if genre_objs:
                            review.genres.set(genre_objs)

                        if created:
                            created_reviews += 1

                except Exception as e:
                    # Only show error modal for actual errors, not for skipped games
                    messages.error(
                        request, f'Error processing {title}: {str(e)}')
                    continue

        # Build success message
        success_message = f'Successfully created {created_reviews} review(s)'
        if skipped_reviews > 0:
            success_message += (f' (skipped {skipped_reviews} '
                                f'existing review(s))')

        messages.success(request, success_message)
        return redirect('reviews:populate_interface')

    except Exception as e:
        messages.error(request, f'Error creating reviews: {str(e)}')
        return redirect('reviews:populate_interface')


@user_passes_test(is_superuser)
def auto_generate_interface(request):
    """Interface for auto-generating reviews"""
    return render(request, 'reviews/auto_generate.html')


@user_passes_test(is_superuser)
@require_http_methods(["POST"])
def auto_generate_reviews_view(request):
    """Auto-generate reviews using the management command"""
    from django.core.management import call_command
    
    try:
        count = int(request.POST.get('count', 50))
        min_score = float(request.POST.get('min_score', 5.0))
        max_score = float(request.POST.get('max_score', 10.0))
        
        # Validate input
        if count <= 0 or count > 100:
            messages.error(request, 'Count must be between 1 and 100')
            return redirect('reviews:auto_generate')
        
        if min_score < 1 or max_score > 10 or min_score >= max_score:
            messages.error(request, 'Invalid score range (1-10, min < max)')
            return redirect('reviews:auto_generate')
        
        # Run the management command
        call_command('auto_generate_reviews',
                     count=count,
                     min_score=min_score,
                     max_score=max_score)
        
        messages.success(
            request,
            f'Successfully generated {count} reviews with scores '
            f'{min_score}-{max_score}!'
        )
        
    except Exception as e:
        messages.error(request, f'Error generating reviews: {str(e)}')
    
    return redirect('reviews:auto_generate')
