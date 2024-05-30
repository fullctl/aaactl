# Generated by Django 4.2.10 on 2024-03-13 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0015_service_cross_promote"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="config",
            field=models.JSONField(
                default=dict, help_text="Service specific configuration for this URL."
            ),
        ),
    ]