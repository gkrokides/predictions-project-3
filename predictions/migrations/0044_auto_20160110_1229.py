# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0043_auto_20160110_1229'),
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
    ]
