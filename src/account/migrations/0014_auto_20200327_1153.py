# Generated by Django 2.2.11 on 2020-03-27 11:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("account", "0013_emailconfirmation_passwordreset")]

    operations = [
        migrations.AlterField(
            model_name="passwordreset",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="password_reset",
                to=settings.AUTH_USER_MODEL,
            ),
        )
    ]
