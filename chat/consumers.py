from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Message, Player, Vote, Room
from channels.generic.websocket import AsyncWebsocketConsumer
import datetime
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
import asyncio


from .syncronous_requests import format_votes, save_message, save_vote, remove_player, handle_timeup, aggregate_votes
    

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        #Begin timer for each round when lobby is made
        while True:
            await asyncio.sleep(240)
            room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
            await handle_timeup(room_obj)
            results = await aggregate_votes(room_obj)
            await self.send(text_data=json.dumps(results))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data, dispatch_uid='receive_json'):
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command')
        player_name = text_data_json.get('player')


        #Message Props
        receiver = text_data_json.get('receiver') or self.room_name
        message = text_data_json.get('message')

        #Vote Props
        votee = text_data_json.get('votee')

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': command,
                'message': message,
                'receiver': receiver,
                'player': player_name,

                'votee': votee
            }
        )


    #### possible responses to receiving info from websocket ####
    async def vote(self, event):
        voter = event['player']
        votee = event['votee']
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)

        await save_vote(event, room_obj)

        #aggregate vote information
        results  = await aggregate_votes(room_obj)

        await self.send(text_data=json.dumps(results))


    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        await save_message(event)
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'receiver': event['receiver'],
            'player': event['player']
        }))
