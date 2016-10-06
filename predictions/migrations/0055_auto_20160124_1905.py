# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0054_auto_20160124_1903'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='id',
        ),
        migrations.AlterField(
            model_name='game',
            name='awayteam',
            field=models.ForeignKey(related_name='awayteam', to='predictions.Team'),
        ),
        migrations.AlterField(
            model_name='game',
            name='hometeam',
            field=models.ForeignKey(related_name='hometeam', to='predictions.Team'),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=250, serialize=False, primary_key=True),
        ),
    ]
