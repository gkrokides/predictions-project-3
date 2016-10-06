# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0052_auto_20160124_1844'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='game',
            name='awayteam',
            field=models.ForeignKey(related_name='awayteam', to='predictions.Team', to_field='name'),
        ),
        migrations.AlterField(
            model_name='game',
            name='hometeam',
            field=models.ForeignKey(related_name='hometeam', to='predictions.Team', to_field='name'),
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(unique=True, max_length=250),
        ),
    ]
