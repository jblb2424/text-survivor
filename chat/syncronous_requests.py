from channels.db import database_sync_to_async


@database_sync_to_async
async def save_message(event):
	player = await Player.objects.get(name=event['player'])
	message_obj = Message(player=player, content=event['message'])
	await message_obj.save()

@database_sync_to_async
async def save_vote(event):
	vote = Vote(voter=event['voter'], votee=event['voter'])
	await vote.save()