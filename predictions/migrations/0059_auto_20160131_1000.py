# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0058_auto_20160124_1934'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='elo_rating_away',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='elo_rating_home',
            field=models.FloatField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='leagues',
            name='gwtotal',
            field=models.IntegerField(default=0, verbose_name='No. Gameweeks', editable=False),
        ),
    ]
