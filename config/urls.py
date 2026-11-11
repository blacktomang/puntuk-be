"""Top-level URL configuration."""

from django.http import JsonResponse
from django.urls import include, path


def healthz(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("v1/auth/", include("apps.accounts.urls")),
    path("v1/auth/social/", include("social_django.urls", namespace="social")),
]
