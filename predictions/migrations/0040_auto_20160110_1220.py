# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0039_auto_20160110_1214'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='leagues',
            options={'ordering': ['short_name'], 'verbose_name': 'League', 'verbose_name_plural': 'Leagues'},
        ),
        migrations.RemoveField(
            model_name='post',
            name='awayteam',
        ),
        migrations.RemoveField(
            model_name='post',
            name='hometeam',
        ),
        migrations.DeleteModel(
            name='CyTeams2016',
        ),
    ]
