from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from asgiref.sync import async_to_sync
import operator
from .models import Message, Player, Vote, Room


@database_sync_to_async
def save_message(event):
	player = Player.objects.get(name=event['player'])
	message_obj = Message(player=player, content=event['message'])
	message_obj.save()

@database_sync_to_async
def save_vote(event, room):
	vote = Vote(voter=event['player'], votee=event['votee'], room=room)
	vote.save()

@sync_to_async
def format_votes(grouped_players):
    ret_dict = {}
    for player in grouped_players:
        ret_dict[player['votee']] = player['total']

    ret_dict['current_loser'] = max(ret_dict.items(), key=operator.itemgetter(1))[0]
    return ret_dict