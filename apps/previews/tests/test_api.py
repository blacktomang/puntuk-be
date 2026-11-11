from unittest.mock import patch

from django.test import Client, TestCase

from apps.accounts.models import User


class PreviewApiTests(TestCase):
    def test_preview_requires_a_session(self) -> None:
        response = Client().post("/v1/previews", data={"url": "https://example.test"})

        self.assertEqual(response.status_code, 403)

    def test_preview_passes_validated_url_to_service(self) -> None:
        user = User.objects.create_user("reader", "reader@example.com", "correct horse battery")
        client = Client()
        client.force_login(user)
        response = client.post("/v1/previews", data={"url": "not-a-url"})

        self.assertEqual(response.status_code, 400)

    @patch("apps.previews.views.build_preview")
    def test_authenticated_preview_returns_service_result(self, build_preview) -> None:
        user = User.objects.create_user("reader", "reader@example.com", "correct horse battery")
        build_preview.return_value = {
            "status": "available",
            "title": "Example",
            "duration": {"seconds": None, "provenance": "unknown", "completeness": "unknown"},
        }
        client = Client()
        client.force_login(user)

        with self.assertLogs("apps.previews.views", level="INFO") as logs:
            response = client.post("/v1/previews", data={"url": "https://example.test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Example")
        build_preview.assert_called_once_with("https://example.test")
        self.assertNotIn("example.test", "\n".join(logs.output))
