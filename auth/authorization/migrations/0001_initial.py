# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-09-21 18:09
from __future__ import unicode_literals

import authorization.fields
import authorization.models
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoyalUser',
            fields=[
                ('id', models.UUIDField(default=authorization.models.generate_uuid, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('vk_id', authorization.fields.CharNullField(blank=True, max_length=32, null=True, unique=True)),
                ('fb_id', authorization.fields.CharNullField(blank=True, max_length=32, null=True, unique=True)),
                ('ok_id', authorization.fields.CharNullField(blank=True, max_length=32, null=True, unique=True)),
                ('go_id', authorization.fields.CharNullField(blank=True, max_length=32, null=True, unique=True)),
                ('login', authorization.fields.CharNullField(blank=True, max_length=32, null=True, unique=True)),
                ('password', models.CharField(max_length=64, verbose_name='password')),
                ('salt', models.CharField(blank=True, max_length=64)),
                ('role', models.CharField(choices=[('user', 'user'), ('manager', 'manager'), ('fabric', 'fabric'), ('service', 'service')], max_length=10)),
                ('refresh_token', models.UUIDField(default=uuid.uuid4)),
            ],
        ),
    ]
