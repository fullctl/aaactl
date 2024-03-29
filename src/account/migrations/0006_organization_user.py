# Generated by Django 2.2.11 on 2020-03-23 08:05

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("account", "0005_organization_organizationuser"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="user",
            field=models.OneToOneField(
                blank=True,
                help_text="If set, designates this organzation as a user's personal organization",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="personal_org",
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
