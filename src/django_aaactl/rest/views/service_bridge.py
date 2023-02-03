from django.contrib.auth import get_user_model
from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import DataViewSet, SystemViewSet
from rest_framework.response import Response

import account.models as account_models
import applications.models as application_models
import billing.models as billing_models
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
class Heartbeat(SystemViewSet):
    ref_tag = "heartbeat"

    @grainy_endpoint("service_bridge.system", explicit=False)
    def list(self, request, *args, **kwargs):
        return Response({"status": "ok"})


@route
class Service(AaactlDataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("group", "group__iexact"),
        ("name", "name__iexact"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = application_models.Service.objects.filter(status="ok")
    serializer_class = Serializers.service_application

    def serializer_context(self, request, context):

        if request.GET.get("org"):
            org = account_models.Organization.objects.get(slug=request.GET.get("org"))
            context.update(org=org)

        return context


@route
class Product(AaactlDataViewSet):
    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("component", "component__name__iexact"),
        ("name", "name__iexact"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = billing_models.Product.objects.filter(status="ok")
    serializer_class = Serializers.product


@route
class OrganizationProduct(AaactlDataViewSet):
    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("component", "product__component__name__iexact"),
        ("name", "product__name__iexact"),
        ("org", "org__slug"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = billing_models.OrganizationProduct.objects.filter(status="ok").order_by(
        "-created"
    )
    serializer_class = Serializers.org_product


@route
class User(AaactlDataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("username", "username__iexact"),
    ]
    allow_unfiltered = False
    autocomplete = "username"

    queryset = get_user_model().objects.all()
    serializer_class = Serializers.user
