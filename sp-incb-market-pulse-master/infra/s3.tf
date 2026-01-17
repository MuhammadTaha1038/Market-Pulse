module "s3_bucket" {
  count  = var.bucket_required ? 1:0
  source  = "git::https://gitlab.ihsmarkit.com/pvr/devops/lib/modules/terraform-aws-modules/s3/aws-s3-bucket-v2.git?ref=v5.x"

  aws_region_secondary = local.dr_enabled
  product              = var.app_prefix
  env                  = var.env
  replication_enabled  = local.dr_enabled
  cors_rule            = {
    "allowed_methods":["PUT", "POST", "DELETE", "GET", "HEAD"],
    "allowed_origins":["https://pvr-ft-cas-portal.*","https://pvr-ci-cas-portal.*","https://pvr-cas-portal.*"],
    "allowed_headers" : ["*"]
    "expose_headers" : ["x-amz-server-side-encryption", "x-amz-meta-custom-header", "x-amz-request-id", "x-amz-id-2", "ETag"]
    "max_age_seconds" : 3000
    }

  bucket_name          = local.bucket_name
  providers            = {
    aws.primary         = aws.primary
    aws.secondary       = aws.secondary
  }
  tags                 = local.common_tags
}

