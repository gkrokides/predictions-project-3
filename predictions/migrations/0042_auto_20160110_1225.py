# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0041_auto_20160110_1222'),
    ]

    operations = [
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
