from django.contrib import admin

from applications.models import Service
from common.admin import BaseAdmin

# Register your models here.


@admin.register(Service)
class ServiceAdmin(BaseAdmin):
    list_display = ("name", "slug", "created")
    search_fields = ("name",)
