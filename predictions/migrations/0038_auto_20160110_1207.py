# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0037_auto_20160110_1200'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='end_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='season',
            name='start_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
