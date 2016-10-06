# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0040_auto_20160110_1220'),
    ]

    operations = [
        migrations.CreateModel(
            name='CyTeams2016',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('team', models.CharField(max_length=100, null=True, verbose_name='Team')),
            ],
            options={
                'ordering': ['team'],
                'verbose_name': 'Teams 2016 Cyprus',
                'verbose_name_plural': 'Teams 2016 Cyprus',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='awayteam',
            field=models.ForeignKey(related_name='awayteam', verbose_name='Away Team', to='predictions.CyTeams2016', null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='hometeam',
            field=models.ForeignKey(related_name='hometeam', verbose_name='Home Team', to='predictions.CyTeams2016', null=True),
        ),
    ]
