# 1. The Provider: Who are we talking to? (AWS)
# Terraform automatically finds your keys in .aws/credentials
provider "aws" {
  region = "ap-south-1"  # Mumbai Region
}

# 2. The Queue: Create a new SQS Queue
resource "aws_sqs_queue" "flux_queue" {
  name                      = "flux-queue-iac"  # "IaC" stands for Infrastructure as Code
  message_retention_seconds = 86400             # Keep messages for 1 day
}

# 3. The Database: Create a DynamoDB Table
resource "aws_dynamodb_table" "flux_orders" {
  name           = "FluxOrdersIAC"
  billing_mode   = "PAY_PER_REQUEST" # Free tier friendly (only pay for what you use)
  hash_key       = "item_id"         # The Primary Key

  attribute {
    name = "item_id"
    type = "S"   # 'S' means String
  }

  tags = {
    Environment = "Production"
    Project     = "FluxOrder"
  }
}

# 4. The Outputs: Tell us the URLs after you build them
output "sqs_url" {
  value = aws_sqs_queue.flux_queue.id
}

output "dynamodb_name" {
  value = aws_dynamodb_table.flux_orders.name
}