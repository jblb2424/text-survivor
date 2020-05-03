from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import operator
from .models import Message, Player, Vote, Room

#A utility file of common synronous actions we need to take
def handle_round_end(ret_dict, room_obj):
	Player.objects.filter(name=ret_dict['current_loser']).delete()
	Vote.objects.filter(room=room_obj).delete()
	room_obj.player_count = room_obj.player_count - 1
	room_obj.game_round = room_obj.game_round + 1
	room_obj.save()

@database_sync_to_async
def save_message(event):
	player = Player.objects.get(name=event['player'])
	message_obj = Message(player=player, content=event['message'])
	message_obj.save()

@database_sync_to_async
def save_vote(event, room):
	#Save only if the player hasn't voted in the current round
	player_voted = Vote.objects.filter(voter=event['player'], game_round=room.game_round).exists()
	if not player_voted:
		v = Vote(voter=event['player'], votee=event['votee'], room=room, game_round=room.game_round)
		v.save()

@database_sync_to_async
def remove_player(loser, room):
	Player.objects.get(name=loser).delete()
	room_obj.player_count = room_obj.player_count - 1
	room_obj.save()


@sync_to_async
def format_votes(grouped_players, all_current_votes, all_current_players, room_obj):
	ret_dict = {}
	for player in grouped_players:
		ret_dict[player['votee']] = player['total']

	ret_dict['current_loser'] = max(ret_dict.items(), key=operator.itemgetter(1))[0]
	if len(all_current_players) <= len(all_current_votes):
		ret_dict['round_over'] = True
		handle_round_end(ret_dict, room_obj)
	return ret_dict

