# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0057_auto_20160124_1930'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='id',
        ),
        migrations.AlterField(
            model_name='team',
            name='name',
            field=models.CharField(max_length=250, unique=True, serialize=False, primary_key=True),
        ),
    ]
