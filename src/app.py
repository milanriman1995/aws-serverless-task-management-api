
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

    if method == "GET" and path and path.startswith("/tasks/"):
        task_id = event.get("pathParameters", {}).get("id")

        if not task_id:
            return response(400, {"error": "Task ID is required"})

        import boto3

        table = boto3.resource("dynamodb").Table(
            os.environ["TASKS_TABLE_NAME"]
        )

        result = table.get_item(
            Key={"task_id": task_id}
        )

        task = result.get("Item")

        if task is None:
            return response(404, {"error": "Task not found"})

        return response(200, task)

    if method == "PATCH" and path and path.startswith("/tasks/"):
        task_id = (event.get("pathParameters") or {}).get("id")

        if not task_id:
            return response(400, {"error": "Task ID is required"})

        try:
            body = json.loads(event.get("body") or "{}")
        except (json.JSONDecodeError, TypeError):
            return response(400, {"error": "Invalid JSON"})

        if not isinstance(body, dict):
            return response(400, {"error": "Expected a JSON object"})

        if set(body) != {"status"}:
            return response(400, {
                "error": "Only the status field can be updated"
            })

        status = body["status"]

        if status not in ("pending", "completed"):
            return response(400, {
                "error": "Status must be pending or completed"
            })

        import boto3
        from botocore.exceptions import ClientError

        table = boto3.resource("dynamodb").Table(
            os.environ["TASKS_TABLE_NAME"]
        )

        try:
            result = table.update_item(
                Key={"task_id": task_id},
                UpdateExpression="SET #status = :status",
                ConditionExpression="attribute_exists(task_id)",
                ExpressionAttributeNames={
                    "#status": "status"
                },
                ExpressionAttributeValues={
                    ":status": status
                },
                ReturnValues="ALL_NEW"
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == (
                "ConditionalCheckFailedException"
            ):
                return response(404, {"error": "Task not found"})
            raise

        return response(200, result["Attributes"])

    if method == "DELETE" and path and path.startswith("/tasks/"):
        task_id = (event.get("pathParameters") or {}).get("id")

        if not task_id:
            return response(400, {"error": "Task ID is required"})

        import boto3
        from botocore.exceptions import ClientError

        table = boto3.resource("dynamodb").Table(
            os.environ["TASKS_TABLE_NAME"]
        )

        try:
            table.delete_item(
                Key={"task_id": task_id},
                ConditionExpression="attribute_exists(task_id)"
            )
        except ClientError as error:
            if error.response["Error"]["Code"] == (
                "ConditionalCheckFailedException"
            ):
                return response(404, {"error": "Task not found"})
            raise

        return response(200, {
            "message": "Task deleted",
            "task_id": task_id
        })

    return response(404, {"error": "Route not found"})

