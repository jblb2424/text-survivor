from django.contrib import admin

from .models import Chat, Message, Player, Room
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Player)
admin.site.register(Room)