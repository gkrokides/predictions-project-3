# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0044_auto_20160110_1229'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CyTeams2016',
        ),
    ]
