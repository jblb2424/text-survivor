from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import operator
from .models import Message, Player, Vote, Room
from django.db.models import Count
import json
import random
import math

#A utility file of common synronous actions we need to take

def transfer_to_bank(room_obj, coins):
	room_obj.bank = room_obj.bank + coins
	room_obj.save()

def reset_player_state(room_obj):
	all_players = Player.objects.filter(room=room_obj)
	for player in all_players:
		room_obj.bank = room_obj.bank + player.bounty
		player.bounty = 0
		player.immunity = False
		player.coins = player.coins + 1
		player.save()
		room_obj.save()
	room_obj.game_round = room_obj.game_round + 1
	room_obj.save()

def handle_points_check(ret_dict, room_obj):
	all_players = Player.objects.filter(room=room_obj)
	leaderboard = {}
	for player in all_players:
		leaderboard[player.name] = player.points

	sorted_scores = sorted(leaderboard.values(), reverse=True)
	#winner if the highest score is sufficient and there is no tie
	if sorted_scores[0] > 3 and sorted_scores[1] != sorted_scores[0]:
		ret_dict['game_over'] = True
		room_obj.game_over = True
		room_obj.save()
		for name, score in leaderboard.items():  # for name, age in dictionary.iteritems():  (for Python 2.x)
			if leaderboard[name] == sorted_scores[0]:
				ret_dict['winner'] = name	
	ret_dict['leaderboard'] = leaderboard

 

def handle_round_end(ret_dict, room_obj): #
	#Send message to group
	
	if len(ret_dict.get('current_losers')) == 0:
		message = 'Nobody voted this round!'
	else:
		message = ', '.join(ret_dict['current_losers']) + ' has been eliminated.'

	ret_dict['round_over'] = True
	ret_dict['receiver'] = room_obj.name
	ret_dict['player'] = 'ANNOUNCEMENT'
	ret_dict['message'] = message
	loser_players = Player.objects.filter(name__in=ret_dict['current_losers'])
	loser_coins = {}


	for player in loser_players:
		loser_coins[player.name] = math.ceil(player.coins / 2) + player.bounty

	for loser in loser_players:
		loser.coins = math.ceil(loser.coins / 2)
		loser.bounty = 0
		loser.save()
	#Give each player 1 coin for new round, plus a share of whoever they killed 
	survivng_players = Player.objects.filter(room=room_obj).exclude(name__in=ret_dict['current_losers'])
	for player in survivng_players:
		player_vote = Vote.objects.get(room=room_obj, voter=player.name, game_round=room_obj.game_round)
		if loser_coins.get(player_vote.votee) is not None: #Player voted the correct person out
			num_voted_for_loser = len(Vote.objects.filter(room=room_obj, votee=player_vote.votee))
			coin_bonus = loser_coins.get(player_vote.votee) // num_voted_for_loser
			player.points = player.points + 1
		else:
			coin_bonus = 0
		player.coins = player.coins + coin_bonus
		player.save()

	reset_player_state(room_obj)
	
	room_obj.save()



def handle_round_end_immunity(ret_dict, room_obj): #
	#Send message to group
	ret_dict['round_over'] = True
	ret_dict['receiver'] = room_obj.name
	ret_dict['player'] = 'ANNOUNCEMENT'
	ret_dict['message'] = ', '.join(ret_dict['current_losers']) + "has been eliminated, but has immunity! They will take half of the voters' coins"

	immunity_players = Player.objects.filter(name__in=ret_dict['current_losers'])
	immunity_players_names = [player.name for player in immunity_players]

	#If the player voted for someone with immunity, give up half their coins
	other_players = Player.objects.filter(room=room_obj).exclude(name__in=ret_dict['current_losers'])
	for player in other_players :
		player_vote = Vote.objects.get(room=room_obj, voter=player.name, game_round=room_obj.game_round)
		immunity_player_object = Player.objects.get(name=player_vote.votee)
		if player_vote.votee in immunity_players_names and not player_vote.is_immunity:
			coins_to_give_up = math.ceil(player.coins / 2)
			player.coins  = player.coins - coins_to_give_up
			immunity_player_object.coins = immunity_player_object.coins + coins_to_give_up
		immunity_player_object.save()	
		immunity_player_object.coins = immunity_player_object.coins
		player.save()

	for player in immunity_players:
		player.points  = player.points + 1
		player.save()

	reset_player_state(room_obj)
	room_obj.save()





def remove_player(loser, room_obj):
	if not Player.objects.filter(name=loser).exists():
		Player.objects.get(name=loser).delete()
		room_obj.player_count = room_obj.player_count - 1
		room_obj.save()

def handle_regular_vote(ret_dict, room_obj, voter):
	ret_dict['player'] = 'ANNOUNCEMENT'
	all_current_votes =  Vote.objects.filter(room=room_obj).values_list('voter', flat=True)
	all_current_players = Player.objects.filter(room=room_obj).values_list('name', flat=True)
	have_not_voted = [player for player in all_current_players if player not in all_current_votes]
	ret_dict_message = voter + ' has voted.'
	ret_dict['receiver'] = room_obj.name
	ret_dict['message'] = ret_dict_message

def format_votes(grouped_players, all_current_players, room_obj, voter):
	ret_dict = {}
	for player in grouped_players:
		ret_dict[player['votee']] = player['total']
	list_of_losers = list()
	if ret_dict:
		max_vote = max(ret_dict.items(), key=operator.itemgetter(1))[1]
		for key, value in ret_dict.items():
			if value == max_vote:
				list_of_losers.append(key)

		ret_dict['current_losers'] = [list_of_losers[random.randint(0, len(list_of_losers) -1 )]] #picks random loser
	
	all_current_votes =  Vote.objects.filter(room=room_obj, game_round=room_obj.game_round)
	round_ended = len(all_current_players) <= len(all_current_votes)
	final_round = len(all_current_players) - len(list_of_losers) == 2 and round_ended

	immunity_voted = False

	if round_ended:
		if ret_dict.get('current_losers'):
			immunity_voted = Player.objects.get(name=ret_dict['current_losers'][0]).immunity
		else: #Corer case in which everyone votes
			ret_dict['current_losers'] = []


	if round_ended and immunity_voted:
		handle_round_end_immunity(ret_dict, room_obj)
		handle_points_check(ret_dict, room_obj)
	elif round_ended:
		handle_round_end(ret_dict, room_obj)
		handle_points_check(ret_dict, room_obj)
	else:
		handle_regular_vote(ret_dict, room_obj, voter)

	ret_dict['type'] = 'receive_vote'
	ret_dict['round'] = room_obj.game_round


	return ret_dict



@database_sync_to_async
def save_message(event, room_name):
	player = Player.objects.get(name=event['player'])
	if (event['receiver'] == room_name):
		receiver = room_name
	else:
		receiver = Player.objects.get(name=event['receiver']).name

	message_obj = Message(player=player, content=event['message'], receiver=receiver)
	message_obj.save()

@database_sync_to_async
def save_vote(event, room):
	#Save only if the player hasn't voted in the current round
	player_voted = Vote.objects.filter(voter=event['player'], game_round=room.game_round).exists()
	if not player_voted:
		is_immunity = event['player'] == event['votee']
		v = Vote(voter=event['player'], votee=event['votee'], room=room, game_round=room.game_round, is_immunity=is_immunity)
		
		player_obj = Player.objects.get(name=event['player'])
		if is_immunity and player_obj.coins >= 5:
			player_obj.immunity = True
			player_obj.coins  = player_obj.coins - 5
			transfer_to_bank(room, 5)
			player_obj.save()

		v.save()

@database_sync_to_async
def aggregate_votes(room_obj, voter):
    all_current_votes =  Vote.objects.filter(room=room_obj, game_round=room_obj.game_round, is_immunity=False)
    all_current_players = Player.objects.filter(room=room_obj)
    grouped = all_current_votes.values('votee').annotate(total=Count('id'))
    results = format_votes(grouped, all_current_players, room_obj, voter)
    return results

@sync_to_async
def handle_timeup(room_obj):
	players = set([i.get('name') for i in Player.objects.filter(room=room_obj).values('name')])
	votes_for_round = set([v.get('voter') for v in Vote.objects.filter(room=room_obj, game_round=room_obj.game_round).values('voter')])
	no_vote_players = players - votes_for_round
	#If you haven't voted, that sucks - you're voting for yourself
	for player in no_vote_players:
		Vote.objects.create(voter=player, votee=player, room=room_obj, game_round=room_obj.game_round)

@sync_to_async
def trade(room_obj, trader_name, tradee_name, coins):
	trader = Player.objects.get(name=trader_name)
	tradee = Player.objects.get(name=tradee_name)
	if trader.coins >= 0:
		trader.coins=trader.coins - coins
		tradee.coins=tradee.coins + coins
		trader.save()
		tradee.save()
	return {'trader': trader.coins, 
			'tradee': tradee.coins, 
			'type': 'receive_trade',
			'trader_name': trader_name, 
			'tradee_name': tradee_name,
			'trade_amount': coins
			}

@sync_to_async
def set_bounty(set_for, bounty_amount, setter):
	setter_player = Player.objects.get(name=setter)
	can_set = setter_player.coins - bounty_amount >= 0
	if can_set:
		set_for_player = Player.objects.get(name=set_for)
		set_for_player.bounty = set_for_player.bounty + bounty_amount
		setter_player.coins = setter_player.coins - bounty_amount
		set_for_player.save()
		setter_player.save()
	return {'new_bounty': set_for_player.bounty, 'set_for': set_for}



#### ACTION ITEMS ---> CARDS AND IMMUNITY ####
@sync_to_async
def see_votes(player, room_obj):
	player_obj = Player.objects.get(name=player)
	if player_obj.coins >= player_obj.voted_for_you_price:
		round_bound = room_obj.game_round - 3
		all_votes = Vote.objects.filter(votee=player, game_round__gte = round_bound, is_immunity = False)
		vote_packet = ['round ' + str(vote.game_round) + ' ' + vote.voter for vote in all_votes]
		if len(vote_packet) == 0:
			vote_packet = ['Nobody has voted for you in the last 3 rounds']
		transfer_to_bank(room_obj, player_obj.voted_for_you_price)
		player_obj.coins = player_obj.coins - player_obj.voted_for_you_price
		player_obj.save()
		return {'all_votes': vote_packet, 'see_votes': True}


@sync_to_async
def see_votes_from_player(player_to_see_votes, room_obj, player):
	player_obj = Player.objects.get(name=player)
	print(player_obj.coins)
	if player_obj.coins >= player_obj.player_vote_price:
		round_bound = room_obj.game_round - 3
		all_votes = Vote.objects.filter(voter=player_to_see_votes, game_round__gte = round_bound)
		vote_packet = ['round ' + str(vote.game_round) + ' ' + vote.votee  if vote.votee != player_to_see_votes else 'round ' + str(vote.game_round) + ' ' + "Used Immunity" for vote in all_votes]
		transfer_to_bank(room_obj, player_obj.player_vote_price)
		player_obj.coins = player_obj.coins - player_obj.player_vote_price
		player_obj.save()
		return {'all_votes': vote_packet, 'see_votes_from_player': True}

@sync_to_async
def activate_immunity(player, room_obj):
	player_obj = Player.objects.get(name=player)
	print(player_obj.coins)
	if player_obj.coins >= 5:
		player_voted = Vote.objects.filter(voter=player, game_round=room_obj.game_round).exists()
		if not player_voted:
			v = Vote(voter=player, votee=player, room=room, game_round=room_obj.game_round, is_immunity=True)
			v.save()
		player_obj.immunity = True
		transfer_to_bank(room_obj, 5)
		player_obj.coins = player_obj.coins - 5
		player_obj.save()

@sync_to_async
def get_messages(target_player, room_obj):
	player_obj = Player.objects.get(name=target_player)
	if player_obj.coins >= player_obj.see_messages_price:
		target_player_obj = Player.objects.get(name=target_player)
		all_messages_sent = Message.objects.filter(player=target_player_obj)
		#I'm dumb and made the player field a model and receiver a string - refactor
		all_messages_received = Message.objects.filter(receiver=target_player)
		all_messages = all_messages_sent | all_messages_received

		ordered_messages = all_messages.order_by('timestamp')
		message_packet = [{'message': message.content, 'receiver': message.receiver, 'sender': message.player.name} for message in ordered_messages][-10:]
		transfer_to_bank(room_obj, player_obj.see_messages_price)
		player_obj.coins = player_obj.coins - player_obj.see_messages_price
		player_obj.save()
		return {'target_player': target_player, 'messages': message_packet, 'message_card': True}

@sync_to_async
def charge_player_for_message(player, room_obj):
	player_obj = Player.objects.get(name=player)
	amount = player_obj.anonymous_price
	transfer_to_bank(room_obj, player_obj.anonymous_price)
	player_obj.coins = player_obj.coins - amount
	player_obj.save()



