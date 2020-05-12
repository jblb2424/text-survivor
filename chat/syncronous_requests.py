from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import operator
from .models import Message, Player, Vote, Room
from django.db.models import Count

#A utility file of common synronous actions we need to take
def handle_round_end(ret_dict, room_obj):
	ret_dict['round_over'] = True
	ret_dict['receiver'] = room_obj.name
	ret_dict['player'] = 'ANNOUNCEMENT'
	ret_dict['message'] = ret_dict['current_loser'] + 'has been eliminated.'
	Player.objects.filter(name=ret_dict['current_loser']).delete()
	Vote.objects.filter(room=room_obj).delete()
	room_obj.player_count = room_obj.player_count - 1
	room_obj.game_round = room_obj.game_round + 1
	room_obj.save()

def handle_game_end(ret_dict, room_obj):
	ret_dict['game_over'] = True
	room_obj.delete()

def remove_player(loser, room_obj):
	if not Player.objects.filter(name=loser).exists():
		Player.objects.get(name=loser).delete()
		room_obj.player_count = room_obj.player_count - 1
		room_obj.save()

def format_votes(grouped_players, all_current_votes, all_current_players, room_obj):
	ret_dict = {}
	for player in grouped_players:
		ret_dict[player['votee']] = player['total']
	ret_dict['current_loser'] = max(ret_dict.items(), key=operator.itemgetter(1))[0]

	remove_player(ret_dict['current_loser'], room_obj)

	if len(all_current_players) <= len(all_current_votes):
		handle_round_end(ret_dict, room_obj)
		# if(len(all_current_players) == 1):
		# 	handle_game_end(ret_dict, room_obj)
	return ret_dict


# @database_sync_to_async
# def check_new_player(player, room_obj):
# 	return Player.objects.filter(name=player, room=room_obj).exists()

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
def aggregate_votes(room_obj):
    all_current_votes =  Vote.objects.filter(room=room_obj)
    all_current_players = Player.objects.filter(room=room_obj)
    grouped = all_current_votes.values('votee').annotate(total=Count('id'))
    results = format_votes(grouped, all_current_votes, all_current_players, room_obj)
    return results

@sync_to_async
def handle_timeup(room_obj):
	players = set([i.get('name') for i in Player.objects.filter(room=room_obj).values('name')])
	votes_for_round = set([v.get('voter') for v in Vote.objects.filter(room=room_obj, game_round=room_obj.game_round).values('voter')])
	no_vote_players = players - votes_for_round
	#If you haven't voted, that sucks - you're voting for yourself
	for player in no_vote_players:
		Vote.objects.create(voter=player, votee=player, room=room_obj, game_round=room_obj.game_round)

