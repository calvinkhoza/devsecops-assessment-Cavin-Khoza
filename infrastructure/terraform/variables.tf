variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "docker_image" {
  description = "Docker image to run on the EC2 instance"
  type        = string
  default     = "devsecops-app:latest"
}

# NEW: Sensitive variables for secrets
variable "database_password" {
  description = "Password for the application database"
  type        = string
  sensitive   = true # This ensures the value is redacted from console output
}

variable "api_key" {
  description = "A third-party API key for the application to use"
  type        = string
  sensitive   = true
}