# pyright: basic

from __future__ import annotations

from typing import cast

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)


class AccountAnonymousThrottle(AnonRateThrottle):
    scope = "account_anon"


class AccountUserThrottle(UserRateThrottle):
    scope = "account_user"


def user_payload(user: User) -> dict[str, str]:
    return {"username": user.username, "email": user.email}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountAnonymousThrottle]

    def post(self, request: Request) -> Response:
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        login(
            cast(HttpRequest, request._request),
            user,
            backend="django.contrib.auth.backends.ModelBackend",
        )
        return Response({"user": user_payload(user)}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountAnonymousThrottle]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=cast(HttpRequest, request._request),
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if not isinstance(user, User):
            return Response(
                {"detail": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST
            )
        login(cast(HttpRequest, request._request), user)
        return Response({"user": user_payload(user)})


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountUserThrottle]

    def post(self, request: Request) -> Response:
        logout(cast(HttpRequest, request._request))
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountAnonymousThrottle, AccountUserThrottle]

    def get(self, request: Request) -> Response:
        user = request.user
        if not isinstance(user, User) or not user.is_authenticated:
            return Response({"authenticated": False})
        return Response({"authenticated": True, "user": user_payload(user)})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountAnonymousThrottle]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(
            data=request.data, context={"request": request._request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AccountAnonymousThrottle]

    def post(self, request: Request, uidb64: str, token: str) -> Response:
        try:
            user_id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, OverflowError, TypeError, ValueError, UnicodeDecodeError):
            return Response(
                {"detail": "Invalid reset request."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid reset request."}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = PasswordResetConfirmSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["password"])
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleLinkStartView(APIView):
    """Start Google OAuth only for an already authenticated account."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountUserThrottle]

    def get(self, request: Request):
        del request
        return redirect(reverse("social:begin", kwargs={"backend": "google-oauth2"}))
