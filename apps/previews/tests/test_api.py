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
