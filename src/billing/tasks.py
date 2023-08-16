from django.core.exceptions import ValidationError
from fullctl.django.models import Task
from fullctl.django.tasks import register

import account.models
import billing.models

__all__ = ["UpdateSubscriptionProductInfo"]


@register
class UpdateSubscriptionProductInfo(Task):
    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_update_subscription_product_info"

    def run(self, subscription_product_id, *args, **kwargs):
        subscription_product = billing.models.SubscriptionProduct.objects.get(
            id=subscription_product_id
        )

        if subscription_product.component_object_id:
            obj = subscription_product.component_object

            if not obj:
                raise ValidationError(
                    f"{subscription_product.component_object_handle} does not exist"
                )

            org = account.models.Organization.objects.filter(id=obj.org_id).first()

            if not org:
                raise ValidationError(
                    f"{subscription_product.component_object_handle} organization does not exist (reach out to devops)"
                )

            if org != subscription_product.subscription.org:
                raise ValidationError(
                    f"{subscription_product.component_object_handle}: {obj.name}'s organization `{org.name} ({org.slug})` does not match subscription organization `{subscription_product.subscription.org.name} ({subscription_product.subscription.org.slug})`"
                )

            org_name = org.name if org else "Unknown Organization"
            subscription_product.component_object_name = (
                f"{subscription_product.component_object.name} ({org_name})"
            )
            subscription_product.save()
