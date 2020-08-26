from django.contrib import admin
from reversion.admin import VersionAdmin as ReversionAdmin

from django_handleref.admin import VersionAdmin


# Register your models here.
class BaseAdmin(VersionAdmin, ReversionAdmin):
    readonly_fields = ("version",)
