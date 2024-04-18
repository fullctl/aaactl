import reversion
from django.db import models
from django.utils.translation import gettext as _

from account.models import Organization
from common.models import HandleRefModel

@reversion.register
class OrganizationWhiteLabeling(HandleRefModel):
    org = models.OneToOneField(
        Organization, on_delete=models.CASCADE
    )
    html_footer = models.TextField(blank=True, null=True)
    css = models.TextField(blank=True, null=True)
    dark_logo_url = models.URLField(
        _("Logo URL"),
        max_length=2000,
        blank=True,
        null=True,
        help_text=_("URL used to display the dark logo on the dashboard."),
    )
    light_logo_url = models.URLField(
        _("Logo URL"),
        max_length=2000,
        blank=True,
        null=True,
        help_text=_("URL used to display the light logo on the dashboard."),
    )
    show_logo = models.BooleanField(
        default=False, help_text=_("Show logo in the services drop down")
    )

    class HandleRef:
        tag = "org_whitelabeling"

    def __str__(self):
        return f"{self.org.name}'s White Labeling"
