from django.db import models
from django.utils.translation import gettext as _
from django_grainy.decorators import grainy_model

from applications.service_bridge import Bridge
from common.models import HandleRefModel

# Create your models here.


@grainy_model("svc")
class Service(HandleRefModel):

    slug = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255, unique=True)

    invite_redirect = models.URLField(max_length=255, null=True, blank=True)
    api_host = models.URLField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "applications_service"
        verbose_name = _("Service Application")
        verbose_name_plural = _("Service Applications")

    class HandleRef:
        tag = "svcapp"

    def __str__(self):
        return self.name

    def bridge(self, org):
        return Bridge(self, org)


@grainy_model("svc")
class ServiceAPIEndpoint(HandleRefModel):

    svcapp = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name="api_endpoint_set",
    )

    name = models.CharField(max_length=24)
    path = models.CharField(max_length=255)

    class Meta:
        db_table = "applications_service_api_endpoint"
        verbose_name = _("API Endpoint")
        verbose_name_plural = _("API Endpoints")

    class HandleRef:
        tag = "svcapp_api"
