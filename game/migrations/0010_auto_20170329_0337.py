# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-29 03:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0009_auto_20170222_1403'),
    ]

    operations = [
        migrations.CreateModel(
            name='Hint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=20)),
                ('content', models.CharField(blank=True, max_length=100)),
                ('pre_questions_count', models.IntegerField(default=0)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='game',
            name='hint_used',
        ),
        migrations.AddField(
            model_name='game',
            name='score',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='game',
            name='source_ip',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='hint',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='hints', to='game.Game'),
        ),
    ]