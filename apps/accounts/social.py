from __future__ import annotations

from typing import Any

from social_core.exceptions import AuthForbidden

from apps.accounts.models import User


def enforce_google_account_policy(
    backend: Any,
    details: dict[str, str],
    response: dict[str, object],
    user: User | None = None,
    **_: object,
) -> None:
    """Prevent unverified or silently email-merged Google identities."""
    if backend.name != "google-oauth2":
        return

    email = details.get("email", "").strip().lower()
    verified = response.get("email_verified", response.get("verified_email", False)) is True
    if not email or not verified:
        raise AuthForbidden(backend, "Google must provide a verified email address.")

    existing = User.objects.filter(email__iexact=email).first()
    if existing is not None and user is None:
        raise AuthForbidden(backend, "Sign in locally and link Google from account settings.")
    if existing is not None and user is not None and existing.pk != user.pk:
        raise AuthForbidden(backend, "This Google email belongs to another account.")
