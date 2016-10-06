# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0033_season'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='season',
            name='short_name',
        ),
        migrations.AddField(
            model_name='season',
            name='league',
            field=models.ForeignKey(verbose_name='League', to_field='short_name', to='predictions.Leagues', null=True),
        ),
        migrations.AlterField(
            model_name='leagues',
            name='short_name',
            field=models.CharField(unique=True, max_length=50),
        ),
    ]
