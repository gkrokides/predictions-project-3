# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0060_remove_team_points'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='prediction_elohist',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='prediction_elol6',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='prediction_gsrs',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='prediction_status_elohist',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='prediction_status_elol6',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='game',
            name='prediction_status_gsrs',
            field=models.CharField(max_length=80, null=True, blank=True),
        ),
    ]
