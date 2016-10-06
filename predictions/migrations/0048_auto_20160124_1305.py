# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0047_auto_20160123_1544'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='team',
            options={'ordering': ['name']},
        ),
        migrations.AddField(
            model_name='game',
            name='result',
            field=models.CharField(max_length=5, null=True),
        ),
    ]
