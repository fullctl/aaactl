# Generated by Django 3.2.20 on 2023-08-16 13:02

import django.db.models.deletion
import django.db.models.manager
import django_handleref.models
from django.db import migrations, models

import billing.models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0038_alter_contactmessage_type"),
        ("billing", "0023_auto_20230816_1247"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="invoiceline",
            name="invoice_number",
        ),
        migrations.RemoveField(
            model_name="invoiceline",
            name="order_number",
        ),
        migrations.RemoveField(
            model_name="orderline",
            name="order_number",
        ),
        migrations.CreateModel(
            name="Order",
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
                    "order_number",
                    models.CharField(
                        default=billing.models.unique_order_id, max_length=255
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="order_set",
                        to="account.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Order",
                "verbose_name_plural": "Orders",
                "db_table": "billing_order",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="Invoice",
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
                    "invoice_number",
                    models.CharField(
                        default=billing.models.unique_invoice_id, max_length=255
                    ),
                ),
                (
                    "order",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoice",
                        to="billing.order",
                    ),
                ),
                (
                    "org",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invoice_set",
                        to="account.organization",
                    ),
                ),
            ],
            options={
                "verbose_name": "Invoice",
                "verbose_name_plural": "Invoices",
                "db_table": "billing_invoice",
            },
            managers=[
                ("handleref", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name="invoiceline",
            name="invoice",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="invoice_line_set",
                to="billing.invoice",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="orderline",
            name="order",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="order_line_set",
                to="billing.order",
            ),
            preserve_default=False,
        ),
    ]
