
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "project2-lambda-dynamodb-write"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.tasks.arn
      }
    ]
  })
}

