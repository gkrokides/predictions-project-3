# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0049_auto_20160124_1338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='points',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
