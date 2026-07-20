from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AWS_INFRA = ROOT / "infra/aws"


def test_s3_blueprint_enforces_private_encrypted_transport() -> None:
    main_tf = (AWS_INFRA / "main.tf").read_text(encoding="utf-8")

    assert 'resource "aws_s3_bucket_public_access_block"' in main_tf
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration"' in main_tf
    assert 'resource "aws_s3_bucket_policy" "require_tls"' in main_tf
    assert '"aws:SecureTransport" = "false"' in main_tf
    assert 'object_ownership = "BucketOwnerEnforced"' in main_tf


def test_s3_blueprint_has_cost_and_destructive_action_controls() -> None:
    main_tf = (AWS_INFRA / "main.tf").read_text(encoding="utf-8")
    variables_tf = (AWS_INFRA / "variables.tf").read_text(encoding="utf-8")

    assert "demo_object_retention_days >= 1" in variables_tf
    assert "demo_object_retention_days <= 365" in variables_tf
    assert 'variable "allow_force_destroy"' in variables_tf
    assert "default     = false" in variables_tf
    assert "force_destroy = var.allow_force_destroy" in main_tf
    assert "depends_on = [aws_s3_bucket_versioning.risk_lake]" in main_tf
