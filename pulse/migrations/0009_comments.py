# Generated by Django 5.1.1 on 2024-10-14 06:09

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0008_authuser_remove_users_user_id_users_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comments',
            fields=[
                ('commnent_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('response', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('answer_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pulse.answers')),
                ('expert', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pulse.users')),
            ],
            options={
                'db_table': 'Comments',
            },
        ),
    ]
