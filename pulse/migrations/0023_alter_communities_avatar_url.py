# Generated by Django 5.1.2 on 2024-10-30 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0022_alter_communities_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='communities',
            name='avatar_url',
            field=models.URLField(blank=True, null=True),
        ),
    ]
