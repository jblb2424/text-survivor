from django.shortcuts import render, redirect
from django.http import JsonResponse
# Create your views here.
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from .models import Room, Player
from django.utils.crypto import get_random_string
import urllib.request
import random
from random_words import RandomWords
User = get_user_model()


def get_last_10_messages(chatId):
    chat = get_object_or_404(Chat, id=chatId)
    return chat.messages.order_by('-timestamp').all()[:10]

def get_current_chat(chatId):
    return get_object_or_404(Chat, id=chatId)


def index(request):
	return render(request, 'chat/index.html')


def load_room(request):
	available_rooms = Room.objects.filter(player_count__lte = 5)
	if len(available_rooms) > 0:
		room = available_rooms[random.randint(0, len(available_rooms) -1 )].name
	else:
		room = get_random_string(length = 5)

	return JsonResponse({'room_id': room})

def room(request, room_name):
	#### Generate Random Username
	from random_words import RandomWords
	rw = RandomWords()
	word1 = rw.random_word()
	word2 = rw.random_word()
	unique_name_word = word1 + "_" + word2
	new_room = Room.objects.get_or_create(name=room_name)[0]
	new_player = Player.objects.create(name=unique_name_word, room=new_room)
	new_room.player_count +=1
	new_room.save()
	survivors = Player.objects.filter(room=new_room).values('name', 'id')
	print(new_room.player_count)
	return render(request, 'chat/room.html', {
		'room_name': room_name,
		'player': unique_name_word,
		'survivors': survivors
	})