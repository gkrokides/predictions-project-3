# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-12-14 07:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0008_auto_20161211_1710'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='game_status',
            field=models.CharField(choices=[('OK', 'OK'), ('PST', 'Postponed'), ('CNC', 'Cancelled')], default='OK', max_length=10),
        ),
    ]