# Generated by Django 5.1.2 on 2024-10-29 17:41

import django.contrib.postgres.indexes
import django.contrib.postgres.search
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0020_communities_communitymembers'),
    ]

    operations = [
        migrations.AddField(
            model_name='communities',
            name='search_vector',
            field=django.contrib.postgres.search.SearchVectorField(blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='communities',
            index=django.contrib.postgres.indexes.GinIndex(fields=['search_vector'], name='Communities_search__e215d5_gin'),
        ),
    ]
