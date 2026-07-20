variable "aws_region" {
  description = "AWS region for the demo data lake."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}(-gov)?-[a-z]+-[0-9]$", var.aws_region))
    error_message = "aws_region must be a valid AWS region identifier."
  }
}

variable "bucket_name" {
  description = "Globally unique S3 bucket name for the risk lake demo."
  type        = string

  validation {
    condition = (
      length(var.bucket_name) >= 3 &&
      length(var.bucket_name) <= 63 &&
      can(regex("^[a-z0-9][a-z0-9.-]*[a-z0-9]$", var.bucket_name)) &&
      !strcontains(var.bucket_name, "..")
    )
    error_message = "bucket_name must satisfy the AWS S3 naming rules used by this blueprint."
  }
}

variable "environment" {
  description = "Environment label used for tagging."
  type        = string
  default     = "portfolio-demo"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.environment))
    error_message = "environment must contain only lowercase letters, digits, and hyphens."
  }
}

variable "demo_object_retention_days" {
  description = "Number of days to retain demo data objects before automatic cleanup."
  type        = number
  default     = 7

  validation {
    condition     = var.demo_object_retention_days >= 1 && var.demo_object_retention_days <= 365
    error_message = "demo_object_retention_days must be between 1 and 365."
  }
}

variable "allow_force_destroy" {
  description = "Allow Terraform to delete a non-empty demo bucket. Keep false unless cleanup is intentional."
  type        = bool
  default     = false
}
