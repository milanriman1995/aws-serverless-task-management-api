
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from src.app import lambda_handler


class TestTaskAPI(unittest.TestCase):

    def make_event(self, method, path, body=None):
        event = {
            "requestContext": {
                "http": {"method": method}
            },
            "rawPath": path
        }

        if body is not None:
            event["body"] = body

        return event

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

    def test_create_task_returns_201(self):
        event = self.make_event(
            "POST",
            "/tasks",
            json.dumps({"title": "Study Terraform"})
        )

        mock_boto3 = MagicMock()
        mock_table = mock_boto3.resource.return_value.Table.return_value

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            with patch.dict(
                os.environ,
                {"TASKS_TABLE_NAME": "test-tasks"}
            ):
                response = lambda_handler(event, None)

        body = json.loads(response["body"])

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(body["title"], "Study Terraform")
        self.assertEqual(body["status"], "pending")
        self.assertIn("task_id", body)

        mock_boto3.resource.assert_called_once_with("dynamodb")
        mock_boto3.resource.return_value.Table.assert_called_once_with(
            "test-tasks"
        )
        mock_table.put_item.assert_called_once_with(
            Item=body,
            ConditionExpression="attribute_not_exists(task_id)"
        )

    def test_create_task_rejects_missing_title(self):
        event = self.make_event(
            "POST",
            "/tasks",
            json.dumps({})
        )

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)

    def test_create_task_rejects_invalid_json(self):
        event = self.make_event(
            "POST",
            "/tasks",
            '{"title":'
        )

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)

    def test_create_task_rejects_non_object_json(self):
        event = self.make_event(
            "POST",
            "/tasks",
            json.dumps(["Study Terraform"])
        )

        response = lambda_handler(event, None)

        self.assertEqual(response["statusCode"], 400)

    def test_list_tasks_returns_items(self):
        event = self.make_event("GET", "/tasks")

        expected_tasks = [
            {
                "task_id": "test-123",
                "title": "Study Terraform",
                "status": "pending"
            }
        ]

        mock_boto3 = MagicMock()
        mock_table = mock_boto3.resource.return_value.Table.return_value
        mock_table.scan.return_value = {
            "Items": expected_tasks
        }

        with patch.dict(sys.modules, {"boto3": mock_boto3}):
            with patch.dict(
                os.environ,
                {"TASKS_TABLE_NAME": "test-tasks"}
            ):
                result = lambda_handler(event, None)

        body = json.loads(result["body"])

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(body["tasks"], expected_tasks)
        mock_table.scan.assert_called_once_with(Limit=50)


if __name__ == "__main__":
    unittest.main()

