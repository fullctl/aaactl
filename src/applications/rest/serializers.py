from rest_framework import serializers

import applications.models as models

from fullctl.django.rest.core import HANDLEREF_FIELDS
from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer

Serializers, register = serializer_registry()

@register
class Service(ModelSerializer):
    class Meta:
        model = models.Service
        fields = ["name", "slug", "api_host", "invite_redirect", "logo"]
