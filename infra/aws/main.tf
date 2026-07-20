terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "finbank-risk-lakehouse"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

resource "aws_s3_bucket" "risk_lake" {
  bucket        = var.bucket_name
  force_destroy = var.allow_force_destroy

  tags = {
    CostControl = "demo"
  }
}

resource "aws_s3_bucket_public_access_block" "risk_lake" {
  bucket = aws_s3_bucket.risk_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "risk_lake" {
  bucket = aws_s3_bucket.risk_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "risk_lake" {
  bucket = aws_s3_bucket.risk_lake.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "risk_lake" {
  bucket = aws_s3_bucket.risk_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "risk_lake" {
  bucket = aws_s3_bucket.risk_lake.id

  depends_on = [aws_s3_bucket_versioning.risk_lake]

  rule {
    id     = "expire-demo-objects"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = var.demo_object_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.demo_object_retention_days
    }
  }
}

resource "aws_s3_bucket_policy" "require_tls" {
  bucket = aws_s3_bucket.risk_lake.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.risk_lake.arn,
          "${aws_s3_bucket.risk_lake.arn}/*",
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}
