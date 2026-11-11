# pyright: basic

import logging

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.previews.serializers import PreviewRequestSerializer
from apps.previews.service import build_preview

logger = logging.getLogger(__name__)


class PreviewUserThrottle(UserRateThrottle):
    scope = "preview_user"


class PreviewIpThrottle(SimpleRateThrottle):
    scope = "preview_ip"

    def get_cache_key(self, request: Request, view: APIView) -> str:
        address = request.META.get("REMOTE_ADDR", "unknown")
        return self.cache_format % {"scope": self.scope, "ident": address}


class PreviewView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PreviewUserThrottle, PreviewIpThrottle]

    def post(self, request: Request) -> Response:
        serializer = PreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = build_preview(serializer.validated_data["url"])
        logger.info(
            "preview_request_completed",
            extra={"preview_status": result.get("status"), "user_id": request.user.pk},
        )
        return Response(result)
