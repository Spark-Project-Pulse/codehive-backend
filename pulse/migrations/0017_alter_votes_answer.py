# Generated by Django 5.1.2 on 2024-10-27 19:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0016_merge_20241027_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='votes',
            name='answer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='pulse.answers'),
        ),
    ]
