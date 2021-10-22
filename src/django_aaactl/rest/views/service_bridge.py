from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import DataViewSet, MethodFilter
from rest_framework.decorators import action
from rest_framework.response import Response

import applications.models as application_models
from common.rest.decorators import grainy_endpoint
from django_aaactl.rest.serializers.service_bridge import Serializers


class AaactlDataViewSet(DataViewSet):

    """
    Extend a new version of the data set view
    in order to use the aaactl grainy_endpoint decorator
    on the list and retrieve methods
    """

    @grainy_endpoint("service_bridge")
    def retrieve(self, request, pk):
        return self._retrieve(request, pk)

    @grainy_endpoint("service_bridge")
    def list(self, request, *args, **kwargs):
        return self._list(request, *args, **kwargs)


@route
class Service(AaactlDataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("group", "group__iexact"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = application_models.Service.objects.filter(status="ok")
    serializer_class = Serializers.svcapp