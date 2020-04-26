from channels.db import database_sync_to_async


@database_sync_to_async
async def save_message(event):
	player = await Player.objects.get(name=event['player'])
	message_obj = Message(player=player, content=event['message'])
	await message_obj.save()