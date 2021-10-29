from rest_framework import serializers

import applications.models as models
from common.rest import HANDLEREF_FIELDS


class Serializers:
    pass


def register(cls):
    if not hasattr(cls, "ref_tag"):
        cls.ref_tag = cls.Meta.model.HandleRef.tag
        cls.Meta.fields += HANDLEREF_FIELDS
    setattr(Serializers, cls.ref_tag, cls)
    return cls


@register
class Service(serializers.ModelSerializer):
    class Meta:
        model = models.Service
        fields = ["name", "slug", "api_host", "invite_redirect"]
