# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-26 03:22
from __future__ import unicode_literals

from django.db import migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='description',
            field=tinymce.models.HTMLField(),
        ),
    ]
