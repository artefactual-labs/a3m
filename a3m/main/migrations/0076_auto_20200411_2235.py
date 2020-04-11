# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0075_userprofile_system_emails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='levelofdescription',
            name='name',
            field=models.CharField(max_length=b'1024'),
        ),
    ]
