# Generated by Django 3.0.5 on 2020-10-25 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0026_player_num_voted_for'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='immunity_price',
            field=models.IntegerField(default=10),
        ),
    ]
