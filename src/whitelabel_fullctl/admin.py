from django.contrib import admin
from .models import OrganizationWhiteLabeling

@admin.register(OrganizationWhiteLabeling)
class OrganizationWhiteLabelingAdmin(admin.ModelAdmin):
    list_display = ('org',)
    search_fields = ('org__name',)
