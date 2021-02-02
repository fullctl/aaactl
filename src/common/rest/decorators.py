import reversion
from django_grainy.decorators import grainy_rest_viewset, grainy_rest_viewset_response


class user_endpoint(object):
    def __call__(self, fn):
        def wrapped(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response(status=401)
            with reversion.create_revision():
                reversion.set_user(request.user)
                return fn(self, request, *args, **kwargs)

        wrapped.__name__ = fn.__name__
        return wrapped


class grainy_endpoint(object):
    def __init__(self, namespace=None, require_auth=True, explicit=True):
        self.namespace = namespace
        self.require_auth = require_auth
        self.explicit = explicit

    def __call__(self, fn):
        decorator = self

        @grainy_rest_viewset_response(
            namespace=decorator.namespace,
            namespace_instance=decorator.namespace,
            explicit=decorator.explicit,
            ignore_grant_all=True,
        )
        def wrapped(self, request, *args, **kwargs):
            if decorator.require_auth and not request.user.is_authenticated:
                return Response(status=401)

            with reversion.create_revision():
                reversion.set_user(request.user)
                return fn(self, request, *args, **kwargs)

        wrapped.__name__ = fn.__name__

        return wrapped
