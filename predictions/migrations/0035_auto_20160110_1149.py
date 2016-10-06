# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0034_auto_20160110_1143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='league',
            field=models.ForeignKey(to='predictions.Leagues', null=True),
        ),
    ]
