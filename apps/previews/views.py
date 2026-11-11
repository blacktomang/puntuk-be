# pyright: basic

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.previews.serializers import PreviewRequestSerializer
from apps.previews.service import build_preview


class PreviewUserThrottle(UserRateThrottle):
    scope = "preview_user"


class PreviewView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PreviewUserThrottle]

    def post(self, request: Request) -> Response:
        serializer = PreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(build_preview(serializer.validated_data["url"]))
