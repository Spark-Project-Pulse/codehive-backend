# Generated by Django 5.1.3 on 2024-12-07 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0038_badge_badgetier_userbadge_userbadgeprogress_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='questions',
            name='view_count',
            field=models.BigIntegerField(default=0),
        ),
    ]
