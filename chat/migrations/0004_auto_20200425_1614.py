# Generated by Django 3.0.5 on 2020-04-25 16:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_delete_chat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chat.Player'),
        ),
    ]
