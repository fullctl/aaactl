# Generated by Django 3.2.8 on 2022-03-04 10:23

import django.db.models.deletion
import django.db.models.manager
import django_handleref.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0022_default_org"),
    ]

    operations = [
        migrations.AddField(
            model_name="managedpermission",
            name="grant_mode",
            field=models.CharField(
                choices=[("auto", "Automatically"), ("restricted", "Restricted")],
                default="auto",
                help_text="How is this permission granted",
                max_length=16,
            ),
        ),
        migrations.CreateModel(
            name="OrganizationManagedPermission",
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
                (
                    "reason",
                    models.CharField(
                        help_text="Reason organization was granted to manage this permission",
                        max_length=255,
                    ),
                ),
                (
                    "managed_permission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="org_managed_perm_set",
                        to="account.managedpermission",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="org_managed_perm_set",
                        to="account.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Managed permission for organization",
                "verbose_name_plural": "Managed permissions for organization",
                "db_table": "account_org_managed_perms",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
    ]