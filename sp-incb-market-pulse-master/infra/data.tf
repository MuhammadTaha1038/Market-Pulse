locals {
  bucket_name = var.bucket_name == null ? replace(var.app_name, "_", "-") : replace(var.bucket_name, "_", "-")
  environment_var = {
    "PYTHON_HANDLER" = "handler.app"
  }
  primary_layer_arn = var.lambda_layer == null ? [] : ["arn:aws:lambda:${var.aws_region_primary}:${data.aws_caller_identity.identity.account_id}:layer:${var.app_prefix}-${var.env}-${var.lambda_layer}"]
  secondary_layer_arn = var.lambda_layer == null ? [] : ["arn:aws:lambda:${var.aws_region_secondary}:${data.aws_caller_identity.identity.account_id}:layer:${var.app_prefix}-${var.env}-${var.lambda_layer}"]
  dr_enabled = var.env == "ft" ? false : var.dr_enabled ? true : false
  lambda_s3_permission_list = var.bucket_required ? (local.dr_enabled ? [
      module.s3_bucket[0].primary_s3_bucket_arn,
      "${module.s3_bucket[0].primary_s3_bucket_arn}/*",
      module.s3_bucket[0].secondary_s3_bucket_arn,
      "${module.s3_bucket[0].secondary_s3_bucket_arn}/*"] : [
      module.s3_bucket[0].primary_s3_bucket_arn,
      "${module.s3_bucket[0].primary_s3_bucket_arn}/*"]) : []
}

data "aws_caller_identity" "identity" {
  provider = "aws.primary"
}

