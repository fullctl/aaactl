from django.contrib import admin

from common.admin import BaseAdmin

from applications.models import Service

# Register your models here.


@admin.register(Service)
class ServiceAdmin(BaseAdmin):
    list_display = ("name", "slug", "created")
    search_fields = ("name",)
