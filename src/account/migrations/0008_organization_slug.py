# Generated by Django 2.2.11 on 2020-03-23 14:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("account", "0007_auto_20200323_0850")]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="slug",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        )
    ]
