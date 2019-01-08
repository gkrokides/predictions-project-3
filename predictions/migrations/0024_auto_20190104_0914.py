# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2019-01-04 07:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0023_game_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountrySM',
            fields=[
                ('country_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('continent', models.CharField(max_length=200)),
                ('fifa_code', models.CharField(max_length=10)),
                ('iso_code', models.CharField(max_length=10)),
                ('flag', models.TextField()),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='tip',
            name='tipster',
            field=models.CharField(choices=[('Alesantro', 'Alesantro'), ('Krok', 'Krok'), ('Mr X', 'Mr X'), ('The Bomber', 'The Bomber'), ('Mr Combo', 'Mr Combo'), ('GG', 'GG'), ('---', '---')], default='---', max_length=15),
        ),
    ]