# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-02-25 07:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0020_auto_20170218_1610'),
    ]

    operations = [
        migrations.AlterField(
            model_name='betslip',
            name='bet_type',
            field=models.CharField(choices=[('Singles', 'Singles'), ('Any 2', 'Any 2'), ('Any 3', 'Any 3'), ('Any 4', 'Any 4'), ('Any 2 or 3', 'Any 2 or 3'), ('Any 3 or 4', 'Any 3 or 4'), ('Any 4 or 5', 'Any 4 or 5'), ('All', 'All'), ('---', '---')], default='---', max_length=15),
        ),
    ]
