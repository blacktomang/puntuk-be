import json

from django.test import Client, TestCase, override_settings


class SwaggerDevelopmentTests(TestCase):
    @override_settings(DEBUG=True)
    def test_openapi_document_defines_routes_and_payloads(self) -> None:
        response = Client().get("/swagger/openapi.json")

        self.assertEqual(response.status_code, 200)
        document = json.loads(response.content)
        self.assertIn("/v1/previews", document["paths"])
        self.assertIn("/v1/auth/register", document["paths"])
        self.assertEqual(document["components"]["schemas"]["PreviewRequest"]["required"], ["url"])

    @override_settings(DEBUG=True)
    def test_swagger_ui_references_local_document(self) -> None:
        response = Client().get("/swagger/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger-ui", response.content.decode())
        self.assertIn("/swagger/openapi.json", response.content.decode())
        self.assertIn("X-CSRFToken", response.content.decode())
        self.assertIn("credentials = 'include'", response.content.decode())
        self.assertNotIn("fetch('/v1/auth/csrf'", response.content.decode())

    @override_settings(DEBUG=False)
    def test_swagger_routes_are_unavailable_when_not_debug(self) -> None:
        client = Client()

        self.assertEqual(client.get("/swagger/").status_code, 404)
        self.assertEqual(client.get("/swagger/openapi.json").status_code, 404)
