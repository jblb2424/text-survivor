# Generated by Django 3.0.5 on 2020-07-19 16:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0023_player_objecttive_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='player',
            old_name='objecttive_state',
            new_name='objective_state',
        ),
    ]