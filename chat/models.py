from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver



class Room(models.Model):
    name = models.CharField(max_length=10)
    player_count = models.IntegerField(default=0)
    game_round = models.IntegerField(default=1)
    public = models.BooleanField(default=True)
    game_over = models.BooleanField(default=False)
    bank = models.IntegerField(default=0)


class Player(models.Model):
    name = models.CharField(max_length=10)
    is_out = models.BooleanField(default=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    coins = models.IntegerField(default=5)
    bounty = models.IntegerField(default=0)
    points = models.IntegerField(default=0)
    immunity = models.BooleanField(default=False)
    anonymous_price = models.IntegerField(default=0)
    voted_for_you_price = models.IntegerField(default=0)
    player_vote_price = models.IntegerField(default=0)
    see_messages_price = models.IntegerField(default=0)


class Message(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player', default=None)
    receiver = models.CharField(max_length=30, default='')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Vote(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    voter = models.CharField(max_length=30)
    votee = models.CharField(max_length=30)
    is_immunity = models.BooleanField(default=False)
    game_round=models.IntegerField(default=1)

    
# @receiver(pre_delete, sender=Player, dispatch_uid='player_delete_signal')
# def log_deleted_question(sender, instance, using, **kwargs):
#     d = Deleted()
#     room = d.room
#     room.player_count -= 1


