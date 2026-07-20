output "bucket_name" {
  value       = aws_s3_bucket.risk_lake.bucket
  description = "Provisioned S3 bucket for bronze/silver/gold lakehouse objects."
}

output "bucket_arn" {
  value       = aws_s3_bucket.risk_lake.arn
  description = "ARN of the provisioned S3 bucket."
}

output "aws_region" {
  value       = var.aws_region
  description = "AWS region selected for the blueprint."
}
