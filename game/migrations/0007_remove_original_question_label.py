# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-16 12:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0006_auto_20170216_1754'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='original_question',
            name='label',
        ),
    ]