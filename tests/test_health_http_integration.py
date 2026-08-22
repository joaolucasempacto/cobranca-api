from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app


class HealthHTTPIntegrationTests(TestCase):
    def test_health_endpoint_with_application_lifespan(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
