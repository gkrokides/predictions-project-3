# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0046_auto_20160123_1350'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='away_team',
            field=models.ForeignKey(related_name='away_team', verbose_name='Away Team', to='predictions.Team', null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='home_team',
            field=models.ForeignKey(related_name='home_team', verbose_name='Home Team', to='predictions.Team', null=True),
        ),
    ]
