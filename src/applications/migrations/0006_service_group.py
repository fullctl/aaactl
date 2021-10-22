# Generated by Django 3.2.8 on 2021-10-21 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0005_service_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="group",
            field=models.CharField(
                blank=True,
                default="fullctl",
                help_text="Put apps in the same group to enable app switching between them",
                max_length=255,
                null=True,
            ),
        ),
    ]