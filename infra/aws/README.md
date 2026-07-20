# AWS S3 Blueprint

This Terraform module is a deployable blueprint for the optional AWS storage path. It is not used by the local
Airflow or Dagster runs, and this repository does not claim that the module has been applied to an AWS account.

It is intentionally small and cost-aware:

- one private S3 bucket for bronze/silver/gold objects;
- bucket versioning for auditability;
- server-side encryption and TLS-only access;
- public access blocked;
- bucket-owner-enforced object ownership;
- lifecycle cleanup for short-lived demo objects.

Run only when you intentionally want to provision cloud resources:

```bash
cd infra/aws
terraform init
terraform fmt -check
terraform validate
terraform plan -var="bucket_name=<globally-unique-demo-bucket>"
```

`terraform plan` and `terraform apply` require valid AWS credentials. Applying the module can incur AWS charges.
`terraform apply` is optional and is not required for the operational local portfolio demo. The default
`allow_force_destroy=false` prevents accidental removal of a non-empty bucket.
