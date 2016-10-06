# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0048_auto_20160124_1305'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='points',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='game',
            name='result',
            field=models.CharField(max_length=5, null=True, blank=True),
        ),
    ]
