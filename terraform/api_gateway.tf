
# Create the HTTP API
resource "aws_apigatewayv2_api" "task_api" {
  name          = "project2-task-management-api"
  protocol_type = "HTTP"
}

# Connect API Gateway to Lambda
resource "aws_apigatewayv2_integration" "lambda" {
  api_id = aws_apigatewayv2_api.task_api.id

  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.task_api.invoke_arn
  payload_format_version = "2.0"
}

# Expose GET /health
resource "aws_apigatewayv2_route" "health" {
  api_id = aws_apigatewayv2_api.task_api.id

  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

# Deploy routes automatically
resource "aws_apigatewayv2_stage" "default" {
  api_id = aws_apigatewayv2_api.task_api.id

  name        = "$default"
  auto_deploy = true
}

# Allow this API route to invoke our Lambda
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayHealthInvocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.task_api.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.task_api.execution_arn}/*/*"
}

# Display the public health endpoint
output "health_endpoint" {
  description = "Public URL for the health endpoint"
  value       = "${aws_apigatewayv2_api.task_api.api_endpoint}/health"
}

resource "aws_apigatewayv2_route" "create_task" {
  api_id = aws_apigatewayv2_api.task_api.id

  route_key = "POST /tasks"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "list_tasks" {
  api_id = aws_apigatewayv2_api.task_api.id

  route_key = "GET /tasks"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_route" "get_task" {
  api_id = aws_apigatewayv2_api.task_api.id

  route_key = "GET /tasks/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

