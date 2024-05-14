# Generated by Django 4.2.10 on 2024-02-21 13:22

import django.db.models.deletion
import django.db.models.manager
import django_handleref.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.OAUTH2_PROVIDER_APPLICATION_MODEL),
        ("account", "0040_invitation_expiry"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuthFederation",
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
                    "application",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organization",
                        to=settings.OAUTH2_PROVIDER_APPLICATION_MODEL,
                        verbose_name="Application",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oauth_applications",
                        to="account.organization",
                        verbose_name="Organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Federation for Organization",
                "verbose_name_plural": "Federation for Organization",
                "db_table": "account_organization_oauth_application",
                "unique_together": {("org", "application")},
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="ServiceFederationSupport",
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
                ("slug", models.CharField(max_length=32, unique=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "federation_level",
                    models.CharField(
                        choices=[
                            ("auth", "Allow org authentication"),
                            ("full", "Full federation"),
                        ],
                        default="auth",
                        help_text="The level of federation for this service.",
                        max_length=255,
                    ),
                ),
            ],
            options={
                "verbose_name": "Federation Support for Service",
                "verbose_name_plural": "Federation Support for Service",
                "db_table": "account_federated_service",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="FederatedServiceURL",
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
                ("url", models.URLField(verbose_name="Service URL")),
                (
                    "auth",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="federated_service_urls",
                        to="account.authfederation",
                        verbose_name="OAuth Application",
                    ),
                ),
                (
                    "service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="urls",
                        to="account.servicefederationsupport",
                        verbose_name="Service",
                    ),
                ),
            ],
            options={
                "verbose_name": "Service URL",
                "verbose_name_plural": "Service URLs",
                "db_table": "account_federated_service_url",
                "unique_together": {("url", "auth"), ("service", "auth")},
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
    ]
