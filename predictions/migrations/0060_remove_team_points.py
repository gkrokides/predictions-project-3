# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0059_auto_20160131_1000'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='points',
        ),
    ]
