# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2017-02-11 17:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0014_tip_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='betslip',
            name='betslip_tipster',
            field=models.CharField(choices=[('Alesantro', 'Alesantro'), ('Krok', 'Krok'), ('Mr X', 'Mr X'), ('The Bomber', 'The Bomber'), ('---', '---')], default='---', max_length=15),
        ),
    ]