from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from .models import Developer
from reviews.models import Review

# Create your views here.


class DeveloperList(generic.ListView):
    """List all developers with pagination"""
    model = Developer
    template_name = "developer/developer_list.html"
    context_object_name = 'developer_list'
    paginate_by = 12

    def get_queryset(self):
        queryset = Developer.objects.all()
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


def developer_games(request, slug):
    """Show all games (reviews) by a specific developer"""
    developer = get_object_or_404(Developer, slug=slug)
    games = Review.objects.filter(developer=developer, is_published=True)

    return render(request, 'developer/developer_games.html', {
        'developer': developer,
        'games': games
    })


def populate_interface(request):
    """Developer populate interface with bulk actions"""
    from django.contrib import messages
    from django.core.paginator import Paginator

    if request.method == 'POST':
        action = request.POST.get('action')
        current_page = request.POST.get(
            'current_page', request.GET.get('page', 1)
        )

        if action == 'delete_selected':
            developer_ids = request.POST.getlist('existing_developer_ids')
            if developer_ids:
                try:
                    deleted_developers = Developer.objects.filter(
                        id__in=developer_ids
                    )
                    count = deleted_developers.count()
                    deleted_developers.delete()
                    messages.success(
                        request, f'Successfully deleted {count} developer(s)'
                    )
                except Exception as e:
                    messages.error(
                        request, f'Error deleting developers: {str(e)}'
                    )
            else:
                messages.warning(request, 'No developers selected')
            # Redirect with pagination
            redirect_url = 'developer:populate_interface'
            if current_page and str(current_page) != '1':
                redirect_url += f'?page={current_page}'
            return redirect(redirect_url)

        elif action == 'delete_unused':
            try:
                # Find developers with 0 games
                unused_developers = [
                    dev for dev in Developer.objects.all()
                    if dev.games_count == 0
                ]
                count = len(unused_developers)
                if count > 0:
                    Developer.objects.filter(
                        id__in=[dev.id for dev in unused_developers]
                    ).delete()
                    messages.success(
                        request,
                        f'Successfully deleted {count} unused developer(s)'
                    )
                else:
                    messages.info(request, 'No unused developers found')
            except Exception as e:
                messages.error(
                    request, f'Error deleting unused developers: {str(e)}'
                )
            return redirect('developer:populate_interface')

    # Get existing developers and add pagination
    existing_developers_queryset = Developer.objects.all().order_by(
        '-created_on'
    )
    paginator = Paginator(existing_developers_queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'developer/populate_developers.html', {
        'developers': [],
        'existing_developers': page_obj,
        'paginator': paginator,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_term': '',
        'limit': 50
    })


def create_developers(request):
    """Placeholder view for creating developers"""
    # This is a placeholder - implement the creation logic here
    return redirect('developer:populate_interface')
