import json
import unittest

from src.app import lambda_handler


class TestTaskAPI(unittest.TestCase):

    def make_event(self, method, path):
        return {
            "requestContext": {
                "http": {
                    "method": method
                }
            },
            "rawPath": path
        }

    def test_health_returns_200(self):
        event = self.make_event("GET", "/health")
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 200)

    def test_health_returns_healthy_status(self):
        event = self.make_event("GET", "/health")
        response = lambda_handler(event, None)
        body = json.loads(response["body"])

        self.assertEqual(body["status"], "healthy")
        self.assertEqual(
            body["service"],
            "task-management-api"
        )

    def test_unknown_route_returns_404(self):
        event = self.make_event("GET", "/unknown")
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 404)

    def test_unsupported_method_returns_404(self):
        event = self.make_event("POST", "/health")
        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 404)


if __name__ == "__main__":
    unittest.main()

