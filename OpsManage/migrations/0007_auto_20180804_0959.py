# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-08-04 09:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('OpsManage', '0006_project_config_service'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project_config',
            name='service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='OpsManage.Service_Assets'),
        ),
    ]
