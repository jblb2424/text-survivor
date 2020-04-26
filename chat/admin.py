from django.contrib import admin

from .models import Message, Player, Room, Vote
admin.site.register(Message)
admin.site.register(Player)
admin.site.register(Room)
admin.site.register(Vote)