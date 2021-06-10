from django.http import Http404, HttpResponse
from django.utils.safestring import mark_safe


def diag(request):
    if not request.user.is_superuser:
        raise Http404()

    return HttpResponse(mark_safe(f"<div>{request.META}</div>"))
