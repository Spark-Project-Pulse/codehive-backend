# Generated by Django 5.1.2 on 2024-11-11 04:07

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0030_rename_userrole_userroles_alter_userroles_table'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userroles',
            name='id',
        ),
        migrations.AddField(
            model_name='userroles',
            name='role_type',
            field=models.CharField(choices=[('user', 'User'), ('admin', 'Admin')], default='user', max_length=5),
        ),
        migrations.AlterField(
            model_name='userroles',
            name='role',
            field=models.OneToOneField(default=uuid.uuid4, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='pulse.users'),
        ),
    ]