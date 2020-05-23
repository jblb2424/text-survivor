from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import operator
from .models import Message, Player, Vote, Room
from django.db.models import Count
import json

#A utility file of common synronous actions we need to take


def handle_round_end(ret_dict, room_obj): #
	#Send message to group
	ret_dict['round_over'] = True
	ret_dict['receiver'] = room_obj.name
	ret_dict['player'] = 'ANNOUNCEMENT'
	ret_dict['message'] = ','.join(ret_dict['current_losers']) + ' has been eliminated.'

	#Delete player from db and reset round state
	Player.objects.filter(name__in=ret_dict['current_losers']).delete()
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

def handle_final_round(ret_dict, room_obj):
	ret_dict['final_round'] = True
	ret_dict['receiver'] = room_obj.name
	ret_dict['player'] = 'ANNOUNCEMENT'
	ret_dict['message'] = ','.join(ret_dict['current_losers']) + ' has been eliminated...but they will decide the winner!'
	room_obj.game_round = room_obj.game_round + 1
	Vote.objects.filter(room=room_obj).delete()
	room_obj.save()

def format_votes(grouped_players, all_current_votes, all_current_players, room_obj):
	ret_dict = {}
	for player in grouped_players:
		ret_dict[player['votee']] = player['total']

	max_vote = max(ret_dict.items(), key=operator.itemgetter(1))[1]
	list_of_losers = list()
	for key, value in ret_dict.items():
		if value == max_vote:
			list_of_losers.append(key)

	ret_dict['current_losers'] = list_of_losers
	round_ended = len(all_current_players) <= len(all_current_votes)
	final_round = len(all_current_players) - len(list_of_losers) == 2 and round_ended
	game_end = len(all_current_players) - len(list_of_losers) == 1 and round_ended

	if final_round:
		handle_final_round(ret_dict, room_obj)
	elif game_end:
		handle_game_end(ret_dict, room_obj)
	elif round_ended:
		handle_round_end(ret_dict, room_obj)

	ret_dict['type'] = 'broadcast'
	return ret_dict



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
    print(results)
    return results

@sync_to_async
def handle_timeup(room_obj):
	players = set([i.get('name') for i in Player.objects.filter(room=room_obj).values('name')])
	votes_for_round = set([v.get('voter') for v in Vote.objects.filter(room=room_obj, game_round=room_obj.game_round).values('voter')])
	no_vote_players = players - votes_for_round
	#If you haven't voted, that sucks - you're voting for yourself
	for player in no_vote_players:
		Vote.objects.create(voter=player, votee=player, room=room_obj, game_round=room_obj.game_round)

