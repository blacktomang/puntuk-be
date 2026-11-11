"""Top-level URL configuration."""

from django.http import JsonResponse
from django.urls import include, path

from apps.core.schema import openapi_json, swagger_ui


def healthz(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("v1/auth/", include("apps.accounts.urls")),
    path("v1/auth/social/", include("social_django.urls", namespace="social")),
    path("v1/", include("apps.previews.urls")),
    path("swagger/", swagger_ui, name="swagger-ui"),
    path("swagger/openapi.json", openapi_json, name="openapi-json"),
]
