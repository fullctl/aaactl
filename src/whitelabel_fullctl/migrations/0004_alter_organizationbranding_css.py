# Generated by Django 4.2.11 on 2024-05-02 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("whitelabel_fullctl", "0003_organizationbranding_http_host"),
    ]

    operations = [
        migrations.AlterField(
            model_name="organizationbranding",
            name="css",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]