output "ec2_public_ip" {
  description = "The public IP address of the EC2 instance hosting the Docker app."
  value       = aws_instance.app_server.public_ip
}

output "rds_endpoint" {
  description = "The database hostname endpoint address for PostgreSQL RDS."
  value       = aws_db_instance.postgres_db.endpoint
}

output "s3_bucket_arn" {
  description = "The ARN of the provisioned Amazon S3 assets bucket."
  value       = aws_s3_bucket.assets_bucket.arn
}

output "s3_bucket_domain" {
  description = "The domain name of the provisioned Amazon S3 assets bucket."
  value       = aws_s3_bucket.assets_bucket.bucket_regional_domain_name
}
