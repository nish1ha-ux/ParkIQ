variable "aws_region" {
  description = "The target AWS region to deploy the ParkIQ infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project prefix for resource names."
  type        = string
  default     = "parkiq"
}

variable "ec2_instance_type" {
  description = "Virtual machine instance size for hosting Docker Compose app."
  type        = string
  default     = "t3.medium"
}

variable "db_instance_class" {
  description = "The database instance type for RDS PostgreSQL."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "Initial relational database name."
  type        = string
  default     = "parkiq_prod"
}

variable "db_user" {
  description = "Administrator username for PostgreSQL RDS."
  type        = string
  default     = "parkiq_admin"
}

variable "db_password" {
  description = "Administrator password for PostgreSQL RDS."
  type        = string
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "Globally unique name for the S3 media and reports bucket."
  type        = string
  default     = "parkiq-cloud-assets-prod-2026"
}
