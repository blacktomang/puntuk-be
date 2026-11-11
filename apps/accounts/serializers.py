# pyright: basic

from __future__ import annotations

from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import AbstractBaseUser
from rest_framework import serializers

from apps.accounts.models import User


class RegistrationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is unavailable.")
        return value

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is unavailable.")
        return value

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        candidate = User(username=attrs["username"], email=attrs["email"])
        password_validation.validate_password(attrs["password"], candidate)
        return attrs

    def create(self, validated_data: dict[str, str]) -> User:
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self) -> None:
        request = self.context["request"]
        form = PasswordResetForm({"email": self.validated_data["email"]})
        if form.is_valid():
            form.save(
                request=request,
                use_https=bool(request.is_secure()),
                from_email=None,
                email_template_name="registration/password_reset_email.txt",
                subject_template_name="registration/password_reset_subject.txt",
            )


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_password(self, value: str) -> str:
        user = self.context["user"]
        if not isinstance(user, AbstractBaseUser):
            raise serializers.ValidationError("Invalid reset request.")
        password_validation.validate_password(value, user)
        return value
