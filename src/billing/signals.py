from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from billing.models import OrganizationProduct

from fullctl.django import auditlog

@receiver(post_save, sender=OrganizationProduct)
def handle_orgproduct_save(sender, **kwargs):

    """
    When a organization is granted access to a product
    through OrganizationProduct ensure any permissions
    granted through the product become managable by
    the organization
    """

    org_product = kwargs.get("instance")

    for managed_permission_grant in org_product.product.managed_permissions.all():
        managed_permission_grant.apply(org_product)

    if kwargs.get("created"):
        with auditlog.Context() as log:
            log.set("org", org_product.org)
            log.log("product_added_to_org", log_object=org_product.product)

@receiver(post_delete, sender=OrganizationProduct)
def handle_orgproduct_delete(sender, **kwargs):

    """
    Create audit log entry `product_removed_from_org` when OrganizationProduct
    instance is deleted
    """

    org_product = kwargs.get("instance")

    with auditlog.Context() as log:
        log.set("org", org_product.org)
        log.log("product_removed_from_org", log_object=org_product.product)
