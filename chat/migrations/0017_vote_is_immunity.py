# Generated by Django 3.0.5 on 2020-06-28 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0016_room_game_over'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='is_immunity',
            field=models.BooleanField(default=False),
        ),
    ]
