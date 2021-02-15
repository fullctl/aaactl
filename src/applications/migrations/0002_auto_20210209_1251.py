# Generated by Django 2.2.17 on 2021-02-09 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="usage_url",
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="service",
            name="invite_redirect",
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
    ]
