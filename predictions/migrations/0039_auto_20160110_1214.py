# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0038_auto_20160110_1207'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cyteams2016',
            name='league',
        ),
        migrations.AddField(
            model_name='leagues',
            name='division',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='leagues',
            name='country',
            field=models.CharField(max_length=200, verbose_name='Country'),
        ),
    ]
