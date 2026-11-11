"""Top-level URL configuration."""

from django.http import JsonResponse
from django.urls import path


def healthz(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [path("healthz", healthz, name="healthz")]
