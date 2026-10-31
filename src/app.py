
import json
import os
import uuid


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method")
    path = event.get("rawPath")

    if method == "GET" and path == "/health":
        return response(200, {
            "status": "healthy",
            "service": "task-management-api"
        })

    if method == "POST" and path == "/tasks":
        try:
            body = json.loads(event.get("body") or "{}")
        except (json.JSONDecodeError, TypeError):
            return response(400, {"error": "Invalid JSON"})

        if not isinstance(body, dict):
            return response(400, {"error": "Expected a JSON object"})

        title = body.get("title")

        if not isinstance(title, str) or not title.strip():
            return response(400, {"error": "Task title is required"})

        task = {
            "task_id": str(uuid.uuid4()),
            "title": title.strip(),
            "status": "pending"
        }

        import boto3

        table = boto3.resource("dynamodb").Table(
            os.environ["TASKS_TABLE_NAME"]
        )

        table.put_item(
            Item=task,
            ConditionExpression="attribute_not_exists(task_id)"
        )

        return response(201, task)

    if method == "GET" and path == "/tasks":
        import boto3

        table = boto3.resource("dynamodb").Table(
            os.environ["TASKS_TABLE_NAME"]
        )

        result = table.scan(Limit=50)

        return response(200, {
            "tasks": result.get("Items", [])
        })

    return response(404, {"error": "Route not found"})

