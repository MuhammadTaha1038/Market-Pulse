module "base_tags" {
  source        = "git::https://gitlab.ihsmarkit.com/pvr/devops/lib/modules/terraform-aws-modules/common-config.git"

  product       = var.app_prefix
  environment   = var.env
  providers = {
    aws = aws.primary
  }
}

locals {
  common_tags   = merge(
  module.base_tags.tags,
  {
    Name = "${var.app_prefix}-${var.env}-${var.app_name}"
    Service = var.app_prefix
    Role = var.app_name
    User = "${var.user_id}@ihsmarkit.com"
    DevOpsModule = "true"
  }
  )
}

