import reversion
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import billing.models as models
from account.rest.decorators import set_org
from billing.rest.route import route
from billing.rest.serializers import Serializers
from common.rest.decorators import grainy_endpoint


@route
class Organization(viewsets.ViewSet):
    ref_tag = "org"

    @set_org
    @grainy_endpoint("org.{org.id}.billing", explicit=False)
    def retrieve(self, request, pk, org):
        return Response({})

    @action(detail=True, methods=["POST"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.contact", explicit=False)
    def billing_setup(self, request, pk, org):

        reversion.set_user(request.user)

        serializer = Serializers.setup(
            data=request.data,
            many=False,
            context={"user": request.user, "org": org, "data": request.data},
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.contact", explicit=False)
    def payment_methods(self, request, pk, org):
        billcon = request.GET.get("billcon")

        if not billcon:
            return Response({"billcon": ["Required field"]}, status=400)

        queryset = models.PaymentMethod.get_for_org(org).filter(billcon_id=billcon)
        serializer = Serializers.pay(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["DELETE"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.contact", explicit=False)
    def payment_method(self, request, pk, org):
        pay = models.PaymentMethod.objects.get(
            billcon__org=org, id=request.data.get("id")
        )

        count = models.PaymentMethod.get_for_org(org).count()

        if pay.billcon.pay_set.filter(status="ok").count() <= 1:
            return Response(
                {
                    "non_field_errors": [
                        "Need at least one payment method set on a billing contact. Delete the billing contact itself if it is no longer needed"
                    ]
                },
                status=400,
            )

        old_id = pay.id
        models.Subscription.set_payment_method(org, replace=pay);
        pay.delete()
        pay.id = old_id
        serializer = Serializers.pay(pay, many=False)


        return Response(serializer.data)

    @action(detail=True, methods=["PUT", "DELETE"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.contact", explicit=False)
    def billing_contact(self, request, pk, org):

        instance = org.billcon_set.get(id=request.data.get("id"))

        if request.method == "PUT":
            serializer = Serializers.billcon(instance=instance, data=request.data)

            if not serializer.is_valid():
                return Response(serializer.errors, status=400)
            serializer.save()

        elif request.method == "DELETE":

            serializer = Serializers.billcon(instance=instance)
            count = models.PaymentMethod.get_for_org(org).count()

            instance.delete()
            models.Subscription.set_payment_method(org)

        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.service", explicit=False)
    def services(self, request, pk, org):
        queryset = models.Subscription.objects.filter(org=org)
        serializer = Serializers.sub(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.service", explicit=False)
    def subscribe(self, request, pk, org):
        name = request.data.get("product")

        try:
            product = models.Product.objects.get(name=name)
        except models.Product.DoesNotExist:
            return Response({"product": [f"Unknown product: {name}"]}, status=400)

        sub = models.Subscription.get_or_create(org, product.group)
        sub.add_prod(product)
        if not sub.cycle:
            sub.start_cycle()

        serializer = Serializers.sub(sub)
        return Response(serializer.data)

    @action(detail=True, methods=["GET"])
    @set_org
    @grainy_endpoint("org.{org.id}.billing.service", explicit=False)
    def orders(self, request, pk, org):
        queryset = models.OrderHistory.objects.filter(billcon__org=org)
        queryset = queryset.prefetch_related("orderitem_set").select_related("billcon")
        queryset = queryset.order_by("-processed")
        serializer = Serializers.order(queryset, many=True)
        return Response(serializer.data)


@route
class Product(viewsets.ViewSet):

    serializer_class = Serializers.prod
    queryset = models.Product.objects.all()

    def list(self, request):
        queryset = models.Product.objects.filter(status="ok")
        serializer = Serializers.prod(queryset, many=True)
        return Response(serializer.data)
