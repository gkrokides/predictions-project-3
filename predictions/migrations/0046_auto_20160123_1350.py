# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0045_delete_cyteams2016'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('gameweek', models.PositiveIntegerField()),
                ('homegoals', models.PositiveIntegerField()),
                ('awaygoals', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250)),
            ],
        ),
        migrations.AlterField(
            model_name='leagues',
            name='gwtotal',
            field=models.IntegerField(default=0, verbose_name="No. Gameweeks (leave this blank. It's an automated field)", editable=False),
        ),
        migrations.AddField(
            model_name='game',
            name='awayteam',
            field=models.ForeignKey(related_name='awayteam', to='predictions.Team'),
        ),
        migrations.AddField(
            model_name='game',
            name='hometeam',
            field=models.ForeignKey(related_name='hometeam', to='predictions.Team'),
        ),
        migrations.AddField(
            model_name='game',
            name='season',
            field=models.ForeignKey(to='predictions.Season'),
        ),
    ]
