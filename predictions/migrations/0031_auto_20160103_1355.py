# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import predictions.models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0030_auto_20160103_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leagues',
            name='gwtotal',
            field=models.IntegerField(default=0, verbose_name='No. Gameweeks'),
        ),
    ]
