# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-01 18:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0007_auto_20160101_2001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='hometeam',
            field=models.ManyToManyField(choices=[('AEK Larnacas', 'AEK Larnacas'), ('Anorthosis', 'Anorthosis'), ('APOEL', 'APOEL'), ('Apollonas', 'Apollonas'), ('AEL', 'AEL'), ('Aris', 'Aris'), ('Omonoia', 'Omonoia'), ('Nea Salamina', 'Nea Salamina'), ('Doxa', 'Doxa'), ('Ermis', 'Ermis'), ('Enwsi Newn Paralimniou', 'Enwsi Newn Paralimniou'), ('Ethnikos Achnas', 'Ethnikos Achnas'), ('Paphos FC', 'Paphos FC'), ('Ayia Napa', 'Ayia Napa')], related_name='_post_hometeam_+', to='predictions.CYLeagueSettings'),
        ),
    ]
