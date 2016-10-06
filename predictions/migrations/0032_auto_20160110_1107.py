# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0031_auto_20160103_1355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cyteams2016',
            options={'ordering': ['team'], 'verbose_name': 'Teams 2016 Cyprus', 'verbose_name_plural': 'Teams 2016 Cyprus'},
        ),
        migrations.AlterModelOptions(
            name='leagues',
            options={'ordering': ['country'], 'verbose_name': 'League', 'verbose_name_plural': 'Leagues'},
        ),
        migrations.AddField(
            model_name='leagues',
            name='country_code',
            field=models.CharField(default='CYP', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leagues',
            name='league_name',
            field=models.CharField(default='Cyprus division 1', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='leagues',
            name='short_name',
            field=models.CharField(default='CYP_DIV_1', max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='leagues',
            name='gwtotal',
            field=models.IntegerField(default=0, verbose_name="No. Gameweeks (leave this blank. It's an automated field)"),
        ),
    ]
