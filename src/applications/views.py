from django.shortcuts import redirect, render
from applications.models import Service

def status(request):
    service_checks = {}

    all_good = True

    for service in Service.objects.filter(status="ok"):
        bridge = service.bridge(None)
        service_checks[service.name] = {}
        try:
            heartbeat = bridge.get("service-bridge/system/heartbeat")[0]
            service_checks[service.name]["heartbeat"] = heartbeat
        except Exception as exc:
            service_checks[service.name]["heartbeat"] = {"status":"failure", "details":str(exc)}
            continue


        try:
            status = bridge.get("service-bridge/system/status")[0]
        except Exception as exc:
            status = {"status-query":{"status":"failure", "details":str(exc)}}

        service_checks[service.name].update(status)

        for name, status in status.items():
            if status.get("status") != "ok":
                all_good = False

    return render(request, "applications/status.html", {"services":service_checks, "all_good":all_good})
