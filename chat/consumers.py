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


from .syncronous_requests import format_votes,save_message, save_vote, remove_player, handle_timeup, aggregate_votes, trade, set_bounty, get_messages, see_votes, see_votes_from_player, activate_immunity, charge_player_for_message
    

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        self.still_voting = True
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        # #Begin timer for each round when lobby is made
        # while self.still_voting
        #     await asyncio.sleep(5)
        #     room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        #     await handle_timeup(room_obj)
        #     results = await aggregate_votes(room_obj)
        #     await self.send(text_data=json.dumps(results))

    async def disconnect(self, close_code):
        # Leave room group
        # await self.channel_layer.group_send(
        #         self.room_group_name,
        #         {'is_dicsconnect': True, 'player': self.player_name, 'type': 'broadcast'}
        # )
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data, dispatch_uid='receive_json'):
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command')
        if command == 'vote':
            await self.vote(text_data_json)
        if command == 'chat_message':
            await self.chat_message(text_data_json)
        if command == 'add_player':
            await self.add_player(text_data_json)
        if command == 'trade':
            await self.trade(text_data_json)
        if command == 'bounty':
            await self.bounty(text_data_json)
        if command == 'message_card':
            await self.message_card(text_data_json)
        if command == 'see_votes':
            await self.see_votes(text_data_json)
        if command == 'see_votes_from_player':
            await self.see_votes_from_player(text_data_json)
        if command == 'activate_immunity':
            await self.activate_immunity(text_data_json)
        if command == 'activate_immunity':
            await self.activate_immunity(text_data_json)
        if command == 'random_vote':
            await self.random_vote(text_data_json)



    async def vote(self, event):
        voter = event['player']
        votee = event['votee']
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        await save_vote(event, room_obj)

        #aggregate vote information
        results  = await aggregate_votes(room_obj, voter)
        player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.send(text_data=json.dumps({'updated_immunity_price': player_obj.immunity_price}))
        await self.channel_layer.group_send(
                self.room_group_name,
                results
        )

    #Occurs when the player is out of time
    async def random_vote(self, event):
        
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        await save_vote(event, room_obj)

        #aggregate vote information
        results  = await aggregate_votes(room_obj, voter)
        await self.channel_layer.group_send(
                self.room_group_name,
                results
        )


    async def chat_message(self, event):
        receiver = event.get('receiver') or self.room_name
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        
        
        message_package = {
            'message': event['message'],
            'receiver': receiver,
            'type': 'broadcast'
        }
        if event.get('is_redacted'):     
            player = 'REDACTED'
            await charge_player_for_message(event['player'], room_obj)
            player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
            await self.send(text_data=json.dumps({'coins': player_obj.coins}))
        else:
            player = event['player']
        
        message_package.update({'player': player})
        await save_message(event, self.room_name)
        await self.update_bank()
        await self.channel_layer.group_send(
            self.room_group_name,
            message_package
        )



    async def add_player(self, event):
        self.player_name = event['player']
        new_player_package = {
            'is_new_player': True,
            'player': event['player'],
            'type': 'broadcast'
        }
        await self.channel_layer.group_send(
            self.room_group_name,
            new_player_package
        )

    async def trade(self, event):
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        executed_trade = await trade(room_obj, event['trader'], event['tradee'], event['coins'])
        await self.channel_layer.group_send(
            self.room_group_name,
            executed_trade
        )

    async def update_bank(self):
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        await self.channel_layer.group_send(
            self.room_group_name, 
            {
            'type': 'broadcast',
            'bank_coins': room_obj.bank
            }
        )

    async def message_card(self, event):
        target_player = event['target_player']
        player = event['player']
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        packet = await get_messages(target_player, room_obj)
        player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.update_bank()
        await sync_to_async(packet.update)({'coins': player_obj.coins})
        await self.send(text_data=json.dumps(packet))

    async def activate_immunity(self, event):
        player = event['player']
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        await activate_immunity(player, room_obj)
        await self.send(text_data=json.dumps({'immunity_activated': True}))
        await self.broadcast({
            'player': 'ANNOUNCEMENT',
            'message': player + ' voted.',
            'receiver': self.room_name
        })

    async def see_votes(self, event):
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        player = event['player']
        packet = await see_votes(player, room_obj)
        player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.update_bank()
        await sync_to_async(packet.update)({'coins': player_obj.coins})
        await self.send(text_data=json.dumps(packet))

    async def see_votes_from_player(self, event):
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        target_player = event['target_player']
        packet = await see_votes_from_player(target_player, room_obj, event['player'])
        player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.update_bank()
        await sync_to_async(packet.update)({'coins': player_obj.coins})
        await self.send(text_data=json.dumps(packet))

    async def bounty(self, event):
        room_obj = await database_sync_to_async(Room.objects.get)(name=self.room_name)
        setter = event['setter']
        set_for = event['set_for']
        bounty_amount = event['bounty_amount']
        bounty_resp = await set_bounty(set_for, bounty_amount, setter)
        await sync_to_async(bounty_resp.update)({'type': 'broadcast'})
        await self.channel_layer.group_send(
            self.room_group_name,
            bounty_resp
        )

        if(self.player_name == event['setter']):
            player = await database_sync_to_async(Player.objects.get)(name=self.player_name)
            await self.send(text_data=json.dumps({'coins': player.coins}))

    #### Receive methods for data response back to player ####
    async def broadcast(self, event):
        package = event
        #player_obj = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.send(text_data=json.dumps(package))


    async def receive_vote(self, event):
        packet = event
        player = await database_sync_to_async(Player.objects.get)(name=self.player_name)
        await self.update_bank()
        await sync_to_async(packet.update)(
            {'coins': player.coins, 
            'points': player.points,
            'objective': player.objective,
            'player_objective': player.player_objective
            }
            )
        await self.send(text_data=json.dumps(packet))


    async def receive_trade(self, event):
        executed_trade = event
        if(self.player_name == event['trader_name']):
            await self.send(text_data=json.dumps({
             'coins': executed_trade['trader'],
             'trade': True,
             'player': 'Trade',
             'message': 'You gave ' + str(event['trade_amount']) + ' coins to ' + event['tradee_name'],
             'receiver': self.room_name
             }
            ))
        if(self.player_name == event['tradee_name']):
            await self.send(text_data=json.dumps({
                'coins': executed_trade['tradee'], 
                'trade': True,
                'player': 'Trade',
                'message': 'You received ' + str(event['trade_amount']) + ' coins from ' +  event['tradee_name'],
                'receiver': self.room_name       
                }))
