variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "culrecords"
}

variable "instance_type" {
  description = "EC2 instance type (t3.micro is AWS Free Tier eligible)"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the AWS EC2 key pair to use for SSH access"
  type        = string
}

variable "public_key_path" {
  description = "Path to the public SSH key file"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the instance. Restrict to your IP for security."
  type        = string
  default     = "0.0.0.0/0"
}

variable "domain_name" {
  description = "Optional domain name for the application. If provided, SSL will be configured."
  type        = string
  default     = ""
}

variable "create_rds" {
  description = "Whether to create an RDS PostgreSQL instance. If false, PostgreSQL runs in Docker on EC2."
  type        = bool
  default     = false
}

variable "db_password" {
  description = "Password for the PostgreSQL database"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "Secret key for the FastAPI backend"
  type        = string
  sensitive   = true
}
