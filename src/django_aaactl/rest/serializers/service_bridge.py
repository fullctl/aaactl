from fullctl.django.rest.decorators import serializer_registry
from fullctl.django.rest.serializers import ModelSerializer

import applications.models as application_models

Serializers, register = serializer_registry()


@register
class Service(ModelSerializer):
    class Meta:
        model = application_models.Service
        fields = ["id", "name", "slug", "invite_redirect", "api_host", "group", "logo"]
