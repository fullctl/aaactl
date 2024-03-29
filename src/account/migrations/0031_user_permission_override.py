# Generated by Django 3.2.14 on 2022-08-16 09:19

import django.db.models.deletion
import django.db.models.manager
import django_grainy.fields
import django_handleref.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("account", "0030_migrate_to_roles"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="managedpermission",
            name="auto_grant_admins",
        ),
        migrations.RemoveField(
            model_name="managedpermission",
            name="auto_grant_users",
        ),
        migrations.CreateModel(
            name="UserPermissionOverride",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "created",
                    django_handleref.models.CreatedDateTimeField(
                        auto_now_add=True, verbose_name="Created"
                    ),
                ),
                (
                    "updated",
                    django_handleref.models.UpdatedDateTimeField(
                        auto_now=True, verbose_name="Updated"
                    ),
                ),
                ("version", models.IntegerField(default=0)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ok", "Ok"),
                            ("pending", "Pending"),
                            ("deactivated", "Deactivated"),
                            ("failed", "Failed"),
                            ("expired", "Expired"),
                        ],
                        default="ok",
                        max_length=12,
                    ),
                ),
                ("namespace", models.CharField(max_length=255)),
                ("permissions", django_grainy.fields.PermissionField()),
                (
                    "org",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permission_overrides",
                        to="account.organization",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="permission_overrides",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "User permission override",
                "verbose_name_plural": "User permission overrides",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
    ]
