# Generated by Django 3.2.4 on 2021-06-21 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0004_auto_20210212_1421"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="logo",
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]