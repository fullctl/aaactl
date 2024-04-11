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
    html_header = models.TextField(blank=True, null=True)
    html_footer = models.TextField(blank=True, null=True)
    css = models.TextField(blank=True, null=True)
    logo_url = models.URLField(
        _("Logo URL"),
        max_length=2000,
        null=True,
        help_text=_("URL used to display the logo on the dashboard."),
    )

    class HandleRef:
        tag = "org_whitelabeling"

    def __str__(self):
        return f"{self.org.name}'s White Labeling"
