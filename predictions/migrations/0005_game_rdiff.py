# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-12-11 08:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0004_auto_20161211_0943'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='rdiff',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
