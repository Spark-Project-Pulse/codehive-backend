# Generated by Django 5.1.3 on 2024-11-25 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pulse', '0036_questions_is_answered'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questions',
            name='is_answered',
            field=models.BooleanField(default=False),
        ),
    ]
