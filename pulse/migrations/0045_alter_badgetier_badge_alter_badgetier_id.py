# Generated by Django 5.1.3 on 2024-12-03 02:11

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0044_auto_alter_badgetier_badgeid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgetier',
            name='badge',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tiers', to='pulse.badge'),
        ),
        migrations.AlterField(
            model_name='badgetier',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
