# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0035_auto_20160110_1149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='season',
            name='league',
            field=models.ForeignKey(related_name='league', to='predictions.Leagues', null=True),
        ),
    ]
