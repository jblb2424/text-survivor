from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

from django.db.models.signals import pre_delete
from django.dispatch import receiver



class Room(models.Model):
    name = models.CharField(max_length=10)
    player_count = models.IntegerField(default=0)


class Player(models.Model):
    name = models.CharField(max_length=10)
    is_out = models.BooleanField(default=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)


class Message(models.Model):
    contact = models.ForeignKey(Player, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.player.name


class Chat(models.Model):
    participants = models.ManyToManyField(
        Player, related_name='chats', blank=True)
    messages = models.ManyToManyField(Message, blank=True)

    def __str__(self):
        return "{}".format(self.pk)



@receiver(pre_delete, sender=Player, dispatch_uid='player_delete_signal')
def log_deleted_question(sender, instance, using, **kwargs):
    d = Deleted()
    room = d.room
    room.player_count -= 1


