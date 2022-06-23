from rest_framework import viewsets
from rest_framework.response import Response

from applications.models import Service
from applications.rest.route import route
from applications.rest.serializers import Serializers


@route
class Services(viewsets.ViewSet):
    serializer_class = Serializers.svcapp
    queryset = Serializers.svcapp.Meta.model.objects.all()

    def list(self, request):
        serializer = Serializers.svcapp(
            Service.objects.filter(status="ok", group="fullctl"),
            many=True,
        )
        return Response(serializer.data)
