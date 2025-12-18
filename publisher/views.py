from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from .models import Publisher
from reviews.models import Review

# Create your views here.


class PublisherList(generic.ListView):
    """List all publishers with pagination"""
    model = Publisher
    template_name = "publisher/publisher_list.html"
    context_object_name = 'publisher_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = Publisher.objects.all()
        sort = self.request.GET.get('sort')
        if sort == 'az':
            queryset = queryset.order_by('name')
        elif sort == 'za':
            queryset = queryset.order_by('-name')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_on')
        elif sort == 'oldest':
            queryset = queryset.order_by('created_on')
        else:
            queryset = queryset.order_by('name')  # Default ordering
        return queryset


def publisher_games(request, slug):
    """Show all games (reviews) by a specific publisher"""
    publisher = get_object_or_404(Publisher, slug=slug)
    games = Review.objects.filter(publisher=publisher, is_published=True)

    return render(request, 'publisher/publisher_games.html', {
        'publisher': publisher,
        'games': games
    })


def populate_interface(request):
    """Publisher populate interface with bulk actions"""
    from django.contrib import messages
    from django.core.paginator import Paginator

    if request.method == 'POST':
        action = request.POST.get('action')
        current_page = request.POST.get(
            'current_page', request.GET.get('page', 1)
        )

        if action == 'delete_selected':
            publisher_ids = request.POST.getlist('existing_publisher_ids')
            if publisher_ids:
                try:
                    deleted_publishers = Publisher.objects.filter(
                        id__in=publisher_ids
                    )
                    count = deleted_publishers.count()
                    deleted_publishers.delete()
                    messages.success(
                        request, f'Successfully deleted {count} publisher(s)'
                    )
                except Exception as e:
                    messages.error(
                        request, f'Error deleting publishers: {str(e)}'
                    )
            else:
                messages.warning(request, 'No publishers selected')
            # Redirect with pagination
            redirect_url = 'publisher:populate_interface'
            if current_page and str(current_page) != '1':
                redirect_url += f'?page={current_page}'
            return redirect(redirect_url)

        elif action == 'delete_unused':
            try:
                # Find publishers with 0 games
                unused_publishers = [
                    pub for pub in Publisher.objects.all()
                    if pub.games_count == 0
                ]
                count = len(unused_publishers)
                if count > 0:
                    Publisher.objects.filter(
                        id__in=[pub.id for pub in unused_publishers]
                    ).delete()
                    messages.success(
                        request,
                        f'Successfully deleted {count} unused publisher(s)'
                    )
                else:
                    messages.info(request, 'No unused publishers found')
            except Exception as e:
                messages.error(
                    request, f'Error deleting unused publishers: {str(e)}'
                )
            return redirect('publisher:populate_interface')

    # Get existing publishers and add pagination
    existing_publishers_queryset = Publisher.objects.all().order_by(
        '-created_on'
    )
    paginator = Paginator(existing_publishers_queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'publisher/populate_publishers.html', {
        'publishers': [],
        'existing_publishers': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_term': '',
        'limit': 50
    })


def create_publishers(request):
    """Placeholder view for creating publishers"""
    # This is a placeholder - implement the creation logic here
    return redirect('publisher:populate_interface')
