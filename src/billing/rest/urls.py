from django.urls import path, include

import billing.rest.views
import billing.rest.route

urlpatterns = [path("", include(billing.rest.route.router.urls))]
