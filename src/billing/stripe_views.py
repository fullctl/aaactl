import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render

from billing.models import BillingContact, PaymentMethod
from billing.payment_processors.stripe import payment_method_name, Stripe

# Set your Stripe secret key here
stripe.api_key = settings.STRIPE_SECRET_KEY

@require_POST
@csrf_exempt
def create_setup_intent(request):
    """Create a SetupIntent and return its client secret."""
    setup_intent = stripe.SetupIntent.create()

    data = {
        'client_secret': setup_intent.client_secret,
        'status': setup_intent.status,
        'id': setup_intent.id
    }
    print()
    print(data)
    print()

    return JsonResponse(data)

@require_POST
@csrf_exempt
def check_setup_intent(request, id):
    """Check if the SetupIntent is successful."""
    setup_intent = stripe.SetupIntent.retrieve(id)

    data = {
        'client_secret': setup_intent.client_secret,
        'status': setup_intent.status,
        'id': setup_intent.id,
        'payment_method': setup_intent.payment_method,
    }
    print()
    print(data)
    print()

    return JsonResponse(data)

def save_payment_method(request, payment_method_id):

    setup_intent_id = request.GET.get('setup_intent')

    setup_intent = stripe.SetupIntent.retrieve(setup_intent_id)

    if setup_intent.status != 'succeeded':
        return render(request, 'billing/setup/stripe-status.html', {
            "setup_intent": setup_intent
        })

    payment_method = PaymentMethod.objects.get(id=payment_method_id)

    assert payment_method.data["stripe_setup_intent"] == setup_intent_id

    payment_method.data['stripe_payment_method'] = setup_intent.payment_method
    payment_method.custom_name = payment_method_name(setup_intent.payment_method)
    payment_method.status = "ok"
    payment_method.save()

    processor = Stripe(payment_method)

    processor.link_customer()


    return render(request, 'billing/setup/stripe-status.html', {
        "setup_intent": setup_intent
    })

