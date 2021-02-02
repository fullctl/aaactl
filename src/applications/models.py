from django.db import models
from django.utils.translation import gettext as _
from django_grainy.decorators import grainy_model

from common.models import HandleRefModel

# Create your models here.


@grainy_model("svc")
class Service(HandleRefModel):

    slug = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255, unique=True)

    invite_redirect = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "applications_service"
        verbose_name = _("Service Application")
        verbose_name_plural = _("Service Applications")

    class HandleRef:
        tag = "svcapp"

    def __str__(self):
        return self.name
