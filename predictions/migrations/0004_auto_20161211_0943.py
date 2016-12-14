# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-12-11 07:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0003_season_teamstotal'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='elo_rating_away_previous_week',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='elo_rating_home_previous_week',
            field=models.FloatField(blank=True, null=True),
        ),
    ]