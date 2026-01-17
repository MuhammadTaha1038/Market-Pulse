module "primary_lambda" {
  source = "git::https://gitlab.ihsmarkit.com/pvr/devops/lib/modules/terraform-aws-modules/lambda/aws-lambda.git?ref=v5.x"

  app_prefix = var.app_prefix
  app_name   = var.app_name
  env        = var.env
  runtime     = var.lambda_runtime
  vpc          = var.vpc
  handler     = var.lambda_handler
  memory_size = var.lambda_memory
  timeout     = var.lambda_timeout
  environment_var = local.environment_var
  is_versioned     = var.is_versioned
  s3_key = "${var.app_name}/${var.release_version != "" ? var.release_version : var.code_version}/${var.lambda_pkg_s3_name}"
  s3_bucket = var.primary_bin_bucket
  host_based_routing        = var.host_based_routing
  routing_weight            = local.dr_enabled  ? (var.aws_region_primary == var.config_region_primary ? var.primary_routing_weight : var.secondary_routing_weight) : var.primary_routing_weight
  code_version    = var.code_version
  release_version = var.release_version
  hostedZoneName  = var.hosted_zone_name
  tags            = local.common_tags
  layers          = local.primary_layer_arn
  providers = {
    aws = aws.primary
  }
}

module "secondary_lambda" {
  source = "git::https://gitlab.ihsmarkit.com/pvr/devops/lib/modules/terraform-aws-modules/lambda/aws-lambda.git?ref=v5.x"
  count      = local.dr_enabled ? 1 : 0
  app_prefix = var.app_prefix
  app_name   = var.app_name
  env        = var.env
  vpc         = var.vpc
  runtime     = var.lambda_runtime
  handler     = var.lambda_handler
  memory_size = var.lambda_memory
  timeout     = var.lambda_timeout
  is_versioned   = var.is_versioned
  environment_var = local.environment_var
  s3_key = "${var.app_name}/${var.release_version != "" ? var.release_version : var.code_version}/${var.lambda_pkg_s3_name}"
  s3_bucket = var.secondary_bin_bucket
  code_version    = var.code_version
  release_version = var.release_version
  host_based_routing        = var.host_based_routing
  routing_weight            = var.aws_region_secondary == var.config_region_secondary ? var.secondary_routing_weight : var.primary_routing_weight
  hostedZoneName  = var.hosted_zone_name
  tags            = local.common_tags
  layers          = local.secondary_layer_arn
  providers = {
    aws = aws.secondary
  }
}

data "aws_iam_policy_document" "lambda_policy_document" {
  count = var.bucket_required ? 1 : 0
  statement {
    actions = [
      "s3:*"
    ]
    effect = "Allow"
    resources = local.lambda_s3_permission_list
  }
  provider = aws.primary
}

data "aws_iam_policy_document" "lambda_policy_document_secondary" {
  count = var.bucket_required && local.dr_enabled ? 1 : 0
  statement {
    actions = [
      "s3:*"
    ]
    effect = "Allow"
    resources = local.lambda_s3_permission_list
  }
  provider = aws.secondary
}


resource "aws_iam_policy" "lambda-policy" {
  count = var.bucket_required ? 1 : 0
  name    = "${var.app_prefix}-${var.env}-${var.aws_region_primary}-${var.app_name}-lambda-policy"
  policy  = data.aws_iam_policy_document.lambda_policy_document[count.index].json
  provider = aws.primary
}

resource "aws_iam_policy" "lambda-policy-secondary" {
  count = var.bucket_required && local.dr_enabled ? 1 : 0
  name    = "${var.app_prefix}-${var.env}-${var.aws_region_secondary}-${var.app_name}-lambda-policy"
  policy  = data.aws_iam_policy_document.lambda_policy_document_secondary[count.index].json
  provider = aws.secondary
}

resource "aws_iam_role_policy_attachment" "primary_lambda_policy_attachment" {
  count = var.bucket_required ? 1 : 0
  role       = module.primary_lambda.lambda_role
  policy_arn = aws_iam_policy.lambda-policy[count.index].arn
  provider = aws.primary
}

resource "aws_iam_role_policy_attachment" "secondary_lambda_policy_attachment" {
  count = var.bucket_required && local.dr_enabled ? 1 : 0
  role       = module.secondary_lambda[0].lambda_role
  policy_arn = aws_iam_policy.lambda-policy-secondary[count.index].arn
  provider = aws.secondary
}

# IAM Policy for SSM Parameter Store access
data "aws_iam_policy_document" "lambda_ssm_policy_document" {
  statement {
    sid = "SSMParameterAccess"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath"
    ]
    effect = "Allow"
    resources = [
      "arn:aws:ssm:${var.aws_region_primary}:*:parameter/${var.app_prefix}/${var.env}/${var.app_name}/oracle/*"
    ]
  }

  statement {
    sid = "KMSDecryptForSSM"
    actions = [
      "kms:Decrypt"
    ]
    effect = "Allow"
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region_primary}.amazonaws.com"]
    }
  }

  provider = aws.primary
}

data "aws_iam_policy_document" "lambda_ssm_policy_document_secondary" {
  count = local.dr_enabled ? 1 : 0
  statement {
    sid = "SSMParameterAccess"
    actions = [
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath"
    ]
    effect = "Allow"
    resources = [
      "arn:aws:ssm:${var.aws_region_secondary}:*:parameter/${var.app_prefix}/${var.env}/${var.app_name}/oracle/*"
    ]
  }

  statement {
    sid = "KMSDecryptForSSM"
    actions = [
      "kms:Decrypt"
    ]
    effect = "Allow"
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.aws_region_secondary}.amazonaws.com"]
    }
  }

  provider = aws.secondary
}

resource "aws_iam_policy" "lambda-ssm-policy" {
  name     = "${var.app_prefix}-${var.env}-${var.aws_region_primary}-${var.app_name}-ssm-policy"
  policy   = data.aws_iam_policy_document.lambda_ssm_policy_document.json
  provider = aws.primary
}

resource "aws_iam_policy" "lambda-ssm-policy-secondary" {
  count    = local.dr_enabled ? 1 : 0
  name     = "${var.app_prefix}-${var.env}-${var.aws_region_secondary}-${var.app_name}-ssm-policy"
  policy   = data.aws_iam_policy_document.lambda_ssm_policy_document_secondary[count.index].json
  provider = aws.secondary
}

resource "aws_iam_role_policy_attachment" "primary_lambda_ssm_policy_attachment" {
  role       = module.primary_lambda.lambda_role
  policy_arn = aws_iam_policy.lambda-ssm-policy.arn
  provider   = aws.primary
}

resource "aws_iam_role_policy_attachment" "secondary_lambda_ssm_policy_attachment" {
  count      = local.dr_enabled ? 1 : 0
  role       = module.secondary_lambda[0].lambda_role
  policy_arn = aws_iam_policy.lambda-ssm-policy-secondary[count.index].arn
  provider   = aws.secondary
}
