from django.urls import path
from . import views

app_name = 'developer'

urlpatterns = [
    path('', views.DeveloperList.as_view(), name='developer_list'),
    path('populate/', views.populate_interface, name='populate_interface'),
    path('populate/create/', views.create_developers,
         name='create_developers'),
    path('<slug:slug>/', views.developer_games, name='developer_games'),
]
