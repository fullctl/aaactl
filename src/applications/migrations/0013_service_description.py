# Generated by Django 3.2.16 on 2023-03-31 15:27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("applications", "0012_alter_service_trial_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="description",
            field=models.TextField(
                blank=True,
                help_text="Service description - will be shown in the service tiles on the dashboard",
                null=True,
            ),
        ),
    ]