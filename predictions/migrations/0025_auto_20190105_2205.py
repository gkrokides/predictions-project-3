# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2019-01-05 20:05
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0024_auto_20190104_0914'),
    ]

    operations = [
        migrations.CreateModel(
            name='FixtureSM',
            fields=[
                ('fixture_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('weather_code', models.CharField(blank=True, max_length=200, null=True)),
                ('weather_type', models.CharField(blank=True, max_length=200, null=True)),
                ('weather_icon', models.TextField(blank=True, null=True)),
                ('attendance', models.IntegerField(null=True)),
                ('pitch_status', models.CharField(blank=True, max_length=200, null=True)),
                ('home_formation', models.CharField(blank=True, max_length=200, null=True)),
                ('away_formation', models.CharField(blank=True, max_length=200, null=True)),
                ('home_goals', models.IntegerField(null=True)),
                ('away_goals', models.IntegerField(null=True)),
                ('ht_score', models.CharField(blank=True, max_length=200, null=True)),
                ('ft_score', models.CharField(blank=True, max_length=200, null=True)),
                ('match_status', models.CharField(blank=True, max_length=200, null=True)),
                ('match_date', models.CharField(blank=True, max_length=200, null=True)),
                ('match_time', models.CharField(blank=True, max_length=200, null=True)),
                ('gameweek', models.IntegerField(null=True)),
                ('stage', models.CharField(blank=True, max_length=200, null=True)),
                ('venue_name', models.CharField(blank=True, max_length=200, null=True)),
                ('venue_surface', models.CharField(blank=True, max_length=200, null=True)),
                ('venue_city', models.CharField(blank=True, max_length=200, null=True)),
                ('venue_capacity', models.IntegerField(null=True)),
                ('venue_image', models.TextField(null=True)),
                ('odds_1', models.FloatField(blank=True, null=True)),
                ('odds_x', models.FloatField(blank=True, null=True)),
                ('odds_2', models.FloatField(blank=True, null=True)),
                ('home_coach', models.CharField(blank=True, max_length=200, null=True)),
                ('home_coach_nationality', models.CharField(blank=True, max_length=200, null=True)),
                ('home_coach_image', models.TextField(blank=True, null=True)),
                ('away_coach', models.CharField(blank=True, max_length=200, null=True)),
                ('away_coach_nationality', models.CharField(blank=True, max_length=200, null=True)),
                ('away_coach_image', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['match_date'],
                'verbose_name': 'SM Fixture',
                'verbose_name_plural': 'SM Fixtures',
            },
        ),
        migrations.CreateModel(
            name='LeagueSM',
            fields=[
                ('league_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('is_cup', models.CharField(blank=True, max_length=200, null=True)),
                ('live_standings', models.CharField(blank=True, max_length=200, null=True)),
                ('topscorer_goals', models.CharField(blank=True, max_length=200, null=True)),
                ('topscorer_assists', models.CharField(blank=True, max_length=200, null=True)),
                ('topscorer_cards', models.CharField(blank=True, max_length=200, null=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'SM League',
                'verbose_name_plural': 'SM Leagues',
            },
        ),
        migrations.CreateModel(
            name='SeasonSM',
            fields=[
                ('season_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('league', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='predictions.LeagueSM')),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'SM Season',
                'verbose_name_plural': 'SM Seasons',
            },
        ),
        migrations.CreateModel(
            name='TeamSM',
            fields=[
                ('team_id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('short_code', models.CharField(blank=True, max_length=200, null=True)),
                ('founded', models.IntegerField(null=True)),
                ('logo_path', models.TextField(blank=True, null=True)),
            ],
            options={
                'ordering': ['name'],
                'verbose_name': 'SM Team',
                'verbose_name_plural': 'SM Teams',
            },
        ),
        migrations.AlterModelOptions(
            name='countrysm',
            options={'ordering': ['name'], 'verbose_name': 'SM Country', 'verbose_name_plural': 'SM Countries'},
        ),
        migrations.AlterField(
            model_name='countrysm',
            name='continent',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='countrysm',
            name='fifa_code',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='countrysm',
            name='flag',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='countrysm',
            name='iso_code',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='teamsm',
            name='country_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='predictions.CountrySM'),
        ),
        migrations.AddField(
            model_name='leaguesm',
            name='country_id',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='predictions.CountrySM'),
        ),
        migrations.AddField(
            model_name='fixturesm',
            name='awayteam',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='awayteam', to='predictions.TeamSM'),
        ),
        migrations.AddField(
            model_name='fixturesm',
            name='hometeam',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hometeam', to='predictions.TeamSM'),
        ),
        migrations.AddField(
            model_name='fixturesm',
            name='season',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='predictions.SeasonSM'),
        ),
    ]
