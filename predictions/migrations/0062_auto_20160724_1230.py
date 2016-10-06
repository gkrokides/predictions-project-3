# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0061_auto_20160320_1509'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='awaygoals',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='homegoals',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
