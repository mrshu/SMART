# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-07-06 13:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_label_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='codebook_file',
            field=models.TextField(default=''),
        ),
    ]