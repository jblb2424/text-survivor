from django.contrib import admin

from .models import Message, Player, Room
admin.site.register(Message)
admin.site.register(Player)
admin.site.register(Room)