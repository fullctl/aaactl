# Generated by Django 3.2.16 on 2023-01-30 12:21

import django.db.models.deletion
import django.db.models.manager
import django_handleref.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0034_impersonation"),
        ("billing", "0014_productpermissiongrant"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="expiry_period",
            field=models.PositiveIntegerField(
                default=0, help_text="Product expires after N days"
            ),
        ),
        migrations.AlterField(
            model_name="subscription",
            name="payment_method",
            field=models.ForeignKey(
                blank=True,
                help_text="User payment option that will be charged by this subscription",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subscription_set",
                to="billing.paymentmethod",
            ),
        ),
        migrations.CreateModel(
            name="OrganizationProduct",
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
                    "expires",
                    models.DateTimeField(
                        blank=True,
                        help_text="Product access expires at this date",
                        null=True,
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        help_text="Products the organization has access to",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="account.organization",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        help_text="Organizations that have access to this product",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organizations",
                        to="billing.product",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        help_text="Product access is granted through this subscription",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applied_product_ownership",
                        to="billing.subscription",
                    ),
                ),
            ],
            options={
                "verbose_name": "Organization Product Access",
                "verbose_name_plural": "Organization Product Access",
                "db_table": "billing_org_product",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
    ]
