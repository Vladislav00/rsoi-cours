# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-02 14:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authorization', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loyaluser',
            name='role',
            field=models.CharField(choices=[('user', 'user'), ('manager', 'manager'), ('fabric', 'fabric'), ('service', 'service')], default='user', max_length=10),
        ),
    ]
