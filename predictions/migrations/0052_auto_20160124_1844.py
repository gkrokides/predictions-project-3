# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0051_points'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='points',
            name='game',
        ),
        migrations.RemoveField(
            model_name='points',
            name='team',
        ),
        migrations.RemoveField(
            model_name='team',
            name='id',
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=250, serialize=False, primary_key=True),
        ),
        migrations.DeleteModel(
            name='Points',
        ),
    ]
