# Generated by Django 3.2.23 on 2023-11-30 17:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0031_alter_billingcontact_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoiceline",
            name="subscription_cycle_product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="invoice_set",
                to="billing.subscriptioncycleproduct",
            ),
        ),
        migrations.AlterField(
            model_name="orderline",
            name="subscription_cycle_product",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="order_set",
                to="billing.subscriptioncycleproduct",
            ),
        ),
    ]
