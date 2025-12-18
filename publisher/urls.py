from django.urls import path
from . import views

app_name = 'publisher'

urlpatterns = [
    path('', views.PublisherList.as_view(), name='publisher_list'),
    path('populate/', views.populate_interface, name='populate_interface'),
    path('populate/create/', views.create_publishers,
         name='create_publishers'),
    path('<slug:slug>/', views.publisher_games, name='publisher_games'),
]
