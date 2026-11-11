from __future__ import annotations

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from social_core.exceptions import AuthForbidden

from apps.accounts.models import User
from apps.accounts.social import enforce_google_account_policy


class AccountApiTests(TestCase):
    def test_register_starts_a_session(self) -> None:
        response = Client().post(
            "/v1/auth/register",
            data={
                "username": "reader",
                "email": "reader@example.com",
                "password": "correct horse battery",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.json()["user"], {"username": "reader", "email": "reader@example.com"}
        )
        self.assertTrue(User.objects.filter(username="reader").exists())

    def test_login_rejects_wrong_password_without_enumerating_user(self) -> None:
        User.objects.create_user(
            username="reader", email="reader@example.com", password="correct horse battery"
        )

        response = Client().post(
            "/v1/auth/login",
            data={"username": "reader", "password": "wrong password"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Invalid username or password."})

    def test_password_reset_changes_password(self) -> None:
        user = User.objects.create_user(
            username="reader", email="reader@example.com", password="correct horse battery"
        )
        client = Client()

        response = client.post(
            "/v1/auth/password-reset",
            data={"email": user.email},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), 1)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = client.post(
            f"/v1/auth/password-reset/{uid}/{token}",
            data={"password": "new correct horse battery"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 204)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new correct horse battery"))

    def test_google_link_requires_session_and_starts_social_flow(self) -> None:
        client = Client()
        self.assertEqual(client.get("/v1/auth/google/link").status_code, 403)

        user = User.objects.create_user(
            username="reader", email="reader@example.com", password="correct horse battery"
        )
        client.force_login(user)
        response = client.get("/v1/auth/google/link")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/v1/auth/social/login/google-oauth2", response["Location"])


class Backend:
    name = "google-oauth2"


class GooglePolicyTests(TestCase):
    def test_rejects_unverified_google_email(self) -> None:
        with self.assertRaises(AuthForbidden):
            enforce_google_account_policy(
                Backend(), {"email": "reader@example.com"}, {"email_verified": False}
            )

    def test_rejects_implicit_merge_with_existing_local_account(self) -> None:
        User.objects.create_user(
            username="reader", email="reader@example.com", password="correct horse battery"
        )

        with self.assertRaises(AuthForbidden):
            enforce_google_account_policy(
                Backend(), {"email": "reader@example.com"}, {"email_verified": True}
            )

    def test_allows_explicit_link_for_the_current_account(self) -> None:
        user = User.objects.create_user(
            username="reader", email="reader@example.com", password="correct horse battery"
        )

        enforce_google_account_policy(
            Backend(), {"email": "reader@example.com"}, {"email_verified": True}, user=user
        )
