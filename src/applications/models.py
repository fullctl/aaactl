from django.db import models
from django.utils.translation import gettext as _
from django_grainy.decorators import grainy_model

from account.models import Organization
from applications.service_bridge import Bridge
from common.models import HandleRefModel

# Create your models here.


@grainy_model("service", namespace_instance="service.{instance.slug}")
class Service(HandleRefModel):

    slug = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255, unique=True)

    invite_redirect = models.URLField(
        _("Service URL"),
        max_length=255,
        null=True,
        help_text=_("URL used to redirect users to the service."),
    )
    api_host = models.URLField(_("API URL"), max_length=255, null=True, blank=True)
    logo = models.URLField(max_length=255, null=True, blank=True)
    group = models.CharField(
        max_length=255,
        default="fullctl",
        blank=True,
        null=True,
        help_text=_("Put apps in the same group to enable app switching between them"),
    )

    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="services",
        help_text=_("Service application is exclusive to this organization"),
    )

    class Meta:
        db_table = "applications_service"
        verbose_name = _("Service Application")
        verbose_name_plural = _("Service Applications")

    class HandleRef:
        tag = "service_application"

    def __str__(self):
        return self.name

    def bridge(self, org):
        return Bridge(self, org)


@grainy_model("service")
class ServiceAPIEndpoint(HandleRefModel):

    service_application = models.ForeignKey(
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
        tag = "service_application_api"
