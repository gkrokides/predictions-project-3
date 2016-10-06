# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0036_auto_20160110_1157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='league',
            field=models.ForeignKey(related_name='league', to_field='short_name', to='predictions.Leagues', null=True),
        ),
    ]
