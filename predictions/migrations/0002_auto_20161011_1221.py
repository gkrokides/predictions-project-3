# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-10-11 09:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='awaygoals',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='game',
            name='homegoals',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
