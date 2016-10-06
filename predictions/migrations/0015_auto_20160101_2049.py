# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-01 18:49
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0014_auto_20160101_2045'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='awayteam',
            field=models.ForeignKey(choices=[('AEK Larnacas', 'AEK Larnacas'), ('Anorthosis', 'Anorthosis'), ('APOEL', 'APOEL'), ('Apollonas', 'Apollonas'), ('AEL', 'AEL'), ('Aris', 'Aris'), ('Omonoia', 'Omonoia'), ('Nea Salamina', 'Nea Salamina'), ('Doxa', 'Doxa'), ('Ermis', 'Ermis'), ('Enwsi Newn Paralimniou', 'Enwsi Newn Paralimniou'), ('Ethnikos Achnas', 'Ethnikos Achnas'), ('Paphos FC', 'Paphos FC'), ('Ayia Napa', 'Ayia Napa')], null=True, on_delete=django.db.models.deletion.CASCADE, related_name='awayteam', to='predictions.CYLeagueSettings'),
        ),
        migrations.RemoveField(
            model_name='post',
            name='hometeam',
        ),
        migrations.AddField(
            model_name='post',
            name='hometeam',
            field=models.ForeignKey(choices=[('AEK Larnacas', 'AEK Larnacas'), ('Anorthosis', 'Anorthosis'), ('APOEL', 'APOEL'), ('Apollonas', 'Apollonas'), ('AEL', 'AEL'), ('Aris', 'Aris'), ('Omonoia', 'Omonoia'), ('Nea Salamina', 'Nea Salamina'), ('Doxa', 'Doxa'), ('Ermis', 'Ermis'), ('Enwsi Newn Paralimniou', 'Enwsi Newn Paralimniou'), ('Ethnikos Achnas', 'Ethnikos Achnas'), ('Paphos FC', 'Paphos FC'), ('Ayia Napa', 'Ayia Napa')], null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hometeam', to='predictions.CYLeagueSettings'),
        ),
    ]
