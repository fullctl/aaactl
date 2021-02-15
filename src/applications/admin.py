from django.contrib import admin

from applications.models import Service, ServiceAPIEndpoint
from common.admin import BaseAdmin

# Register your models here.


class ServiceAPIEndpointInline(admin.TabularInline):
    model = ServiceAPIEndpoint


@admin.register(Service)
class ServiceAdmin(BaseAdmin):
    list_display = ("name", "slug", "created")
    search_fields = ("name",)
    inlines = (ServiceAPIEndpointInline,)
