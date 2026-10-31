
# Package the Python application
data "archive_file" "lambda_package" {
  type        = "zip"
  source_file = "${path.module}/../src/app.py"
  output_path = "${path.module}/lambda.zip"
}

# Allow the Lambda service to assume this IAM role
resource "aws_iam_role" "lambda_execution" {
  name = "project2-task-api-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Create a log group with 7-day retention
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/project2-task-api"
  retention_in_days = 7
}

# Grant permission to write to this log group
resource "aws_iam_role_policy" "lambda_logging" {
  name = "project2-lambda-logging"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.lambda_logs.arn}:*"
      }
    ]
  })
}

# Deploy the Lambda function
resource "aws_lambda_function" "task_api" {
  function_name = "project2-task-api"

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  role    = aws_iam_role.lambda_execution.arn
  handler = "app.lambda_handler"
  runtime = "python3.12"

  timeout     = 10
  memory_size = 128

  environment {
    variables = {
      TASKS_TABLE_NAME = aws_dynamodb_table.tasks.name
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_logging,
    aws_cloudwatch_log_group.lambda_logs,
    aws_iam_role_policy.lambda_dynamodb
  ]
}

