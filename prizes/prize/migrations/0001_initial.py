# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-02 06:01
from __future__ import unicode_literals

from django.db import migrations, models
import prize.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.UUIDField(default=prize.models.generate_uuido, editable=False, primary_key=True, serialize=False)),
                ('prize', models.UUIDField()),
                ('user', models.UUIDField()),
                ('user_contacts', models.CharField(max_length=512)),
            ],
        ),
        migrations.CreateModel(
            name='Prize',
            fields=[
                ('id', models.UUIDField(default=prize.models.generate_uuidp, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128)),
                ('pic', models.ImageField(default='prizeimg/no-img.jpg', upload_to='')),
                ('cost', models.PositiveIntegerField(default=0)),
                ('provider', models.CharField(max_length=128)),
            ],
        ),
    ]
