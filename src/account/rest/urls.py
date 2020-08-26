from django.urls import path, include

import account.rest.views
import account.rest.route

urlpatterns = [path("", include(account.rest.route.router.urls))]
