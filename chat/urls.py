# chat/urls.py
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('load_room/', views.load_room, name='load_room'),
    path('<str:room_name>/', views.room, name='room'),
]