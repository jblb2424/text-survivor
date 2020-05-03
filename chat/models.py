from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver



class Room(models.Model):
    name = models.CharField(max_length=10)
    player_count = models.IntegerField(default=0)
    game_round = models.IntegerField(default=0)


class Player(models.Model):
    name = models.CharField(max_length=10)
    is_out = models.BooleanField(default=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)


class Message(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Vote(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    voter = models.CharField(max_length=30)
    votee = models.CharField(max_length=30)
    game_round=models.IntegerField(default=0)

    
# @receiver(pre_delete, sender=Player, dispatch_uid='player_delete_signal')
# def log_deleted_question(sender, instance, using, **kwargs):
#     d = Deleted()
#     room = d.room
#     room.player_count -= 1


