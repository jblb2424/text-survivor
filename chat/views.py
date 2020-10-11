from django.shortcuts import render, redirect
from django.http import JsonResponse
# Create your views here.
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from .models import Room, Player
from django.utils.crypto import get_random_string
import urllib.request
import random
from django.views.decorators.csrf import csrf_exempt
from random_words import RandomWords
from django.core import serializers
User = get_user_model()
import json
from django.conf import settings as conf_settings
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    DestroyAPIView,
    UpdateAPIView
)
from django.shortcuts import redirect

def view_404(request, exception=None):
    return redirect('')

def index(request):
	print(request.session)
	#request.session.clear()
	domain = conf_settings.DOMAIN
	return render(request, 'chat/index.html', {'domain': domain})


#Tries to find an availible room, and will create a public room if it can't find any
def load_room(request):
	available_rooms = Room.objects.filter(player_count__lt = 6, public=True, game_over=False)

	if len(available_rooms) > 0:
		room = available_rooms[random.randint(0, len(available_rooms) -1 )].name
	else:
		room = get_random_string(length = 5)
	
	new_room = Room.objects.get_or_create(name=room)[0]
	return JsonResponse({'room_id': room})


def create_public_room(request):
	#request.session.clear()
	room = get_random_string(length = 5)
	new_room = Room.objects.create(name=room)
	return JsonResponse({'room_id': room})

def create_private_room(request):
	#request.session.clear()
	room = get_random_string(length = 5)
	new_room = Room.objects.create(name=room, public=False)
	return JsonResponse({'room_id': room})

def room(request, room_name):
	print('view hitting')
	print(request)
	anonymous_price = random.randint(1, 2)
	player_vote_price = random.randint(3, 7)
	voted_for_you_price = random.randint(3, 7)
	see_messages_price = random.randint(5, 9)

	room_exists = Room.objects.filter(name=room_name, game_over=False).exists()
	is_in_room = request.session.get(room_name)
	if not room_exists:
		return redirect('/')

	room = Room.objects.get(name=room_name)
	if room.player_count >= 6 and not is_in_room:
		return redirect('/')
	
	if request.session.get(room_name):
		current_player = request.session.get(room_name)
	else: 
		rw = RandomWords()
		word1 = rw.random_word()
		word2 = rw.random_word()
		unique_name_word = word1 + "_" + word2
		while len(unique_name_word) > 18:
			word1 = rw.random_word()
			word2 = rw.random_word()
			unique_name_word = word1 + "_" + word2


		new_player = Player.objects.create(name=unique_name_word, room=room)
		new_player.anonymous_price = anonymous_price
		new_player.voted_for_you_price = voted_for_you_price
		new_player.player_vote_price = player_vote_price
		new_player.see_messages_price = see_messages_price
		new_player.save()

		request.session[room_name] = unique_name_word
		room.player_count +=1
		room.save()
		current_player = unique_name_word

	survivors = Player.objects.filter(room=room)
	survivor_list = [{'name': survivor.name} for survivor in survivors]
	player = Player.objects.get(name = current_player)
	return render(request, 'chat/room.html', {
		'room_name': room_name,
		'player': current_player,
		'survivors': survivor_list,
		'anonymous_price': player.anonymous_price,
		'voted_for_you_price': player.voted_for_you_price,
		'player_vote_price': player.player_vote_price,
		'see_messages_price': player.see_messages_price
	})

#Fix this
@csrf_exempt
def remove_player(request):
	player = request.POST.get("player")
	Player.objects.get(name=player).delete()
	#What to return in the response?
	return JsonResponse({'status': 200})
