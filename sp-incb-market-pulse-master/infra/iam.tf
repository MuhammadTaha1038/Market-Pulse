data "aws_iam_policy_document" "lambda_policy_document" {
  count = var.bucket_required ? 1 : 0
  statement {
    actions = [
      "s3:*"
    ]
    effect    = "Allow"
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
    effect    = "Allow"
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