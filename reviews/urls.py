from . import views
from .admin_views import approve_comments, approve_reviews
from .populate_views import (populate_reviews_interface,
                             create_reviews_from_selection,
                             auto_generate_interface,
                             auto_generate_reviews_view)
from django.urls import path

app_name = 'reviews'

urlpatterns = [
    path('', views.ReviewList.as_view(), name='review_list'),
    path('search/', views.search_games, name='search_games'),
    path('accounts/profile/', views.profile, name='profile'),
    path('populate/', populate_reviews_interface, name='populate_interface'),
    path('populate/create/', create_reviews_from_selection,
         name='create_reviews'),
    path('auto-generate/', auto_generate_interface, name='auto_generate'),
    path('auto-generate/create/', auto_generate_reviews_view, 
         name='auto_generate_create'),
    path('admin/approve-comments/', approve_comments, name='approve_comments'),
    path('admin/approve-reviews/', approve_reviews, name='approve_reviews'),
    path('<slug:slug>/', views.review_details, name='review_detail'),
    path('<slug:slug>/edit_comment/<int:comment_id>',
         views.user_comment_edit, name='user_comment_edit'),
    path('<slug:slug>/delete_comment/<int:comment_id>',
         views.user_comment_delete, name='user_comment_delete'),
    path('<slug:slug>/edit_review/<int:review_id>',
         views.user_review_edit, name='user_review_edit'),
    path('<slug:slug>/delete_review/<int:review_id>',
         views.user_review_delete, name='user_review_delete'),
]
