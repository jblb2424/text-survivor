# chat/urls.py
from django.urls import path

from . import views
handler404 = 'chat.views.view_404' 
urlpatterns = [
    path('', views.index, name='index'),
    path('create_public_room/', views.create_public_room, name='create_public_room'),
    path('create_private_room/', views.create_private_room, name='create_private_room'),
    path('load_room/', views.load_room, name='load_room'),
    path('remove_player/', views.remove_player, name='remove_player'),
    path('<str:room_name>/', views.room, name='room'),
]