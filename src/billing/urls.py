from django.urls import path

import billing.views

urlpatterns = [
    # path("setup/test/", billing.views.setup_test, name="setup-test"),
    path("setup/", billing.views.setup, name="setup"),
    path("services/", billing.views.services, name="services"),
    path(
        "billing-contacts/<int:id>/",
        billing.views.billing_contact,
        name="billing-contact",
    ),
    path("billing-contacts/", billing.views.billing_contacts, name="billing-contacts"),
    path(
        "order_history-history/details/<str:id>/",
        billing.views.order_history_details,
        name="order_history-history-details",
    ),
    path("order_history-history/", billing.views.order_history, name="order_history-history"),
]
