locals {
  bucket_name = var.bucket_name == null ? replace(var.app_name, "_", "-") : replace(var.bucket_name, "_", "-")
  environment_var = {
    "PYTHON_HANDLER"      = "handler.app"
    "OUTPUT_DESTINATION"  = "s3"
    "S3_BUCKET_NAME"      = local.bucket_name
    "S3_REGION"           = var.aws_region_primary
    "S3_PREFIX"           = "processed_colors/"
    "S3_FILE_FORMAT"      = "parquet"
    "ENVIRONMENT"         = var.env
    "ENABLE_CRON_JOBS"    = "true"
    "CRON_SCHEDULE"       = "0 8,10,12,14,16,18 * * *"
    "CRON_TIMEZONE"       = "UTC"
  }
  primary_layer_arn   = var.lambda_layer == null ? [] : ["arn:aws:lambda:${var.aws_region_primary}:${data.aws_caller_identity.identity.account_id}:layer:${var.app_prefix}-${var.env}-${var.lambda_layer}"]
  secondary_layer_arn = var.lambda_layer == null ? [] : ["arn:aws:lambda:${var.aws_region_secondary}:${data.aws_caller_identity.identity.account_id}:layer:${var.app_prefix}-${var.env}-${var.lambda_layer}"]
  dr_enabled          = var.env == "ft" ? false : var.dr_enabled ? true : false
  lambda_s3_permission_list = var.bucket_required ? (local.dr_enabled ? [
      module.s3_bucket[0].primary_s3_bucket_arn,
      "${module.s3_bucket[0].primary_s3_bucket_arn}/*",
      module.s3_bucket[0].secondary_s3_bucket_arn,
      "${module.s3_bucket[0].secondary_s3_bucket_arn}/*"] : [
      module.s3_bucket[0].primary_s3_bucket_arn,
      "${module.s3_bucket[0].primary_s3_bucket_arn}/*"]) : []
}

data "aws_caller_identity" "identity" {
  provider = aws.primary
}

