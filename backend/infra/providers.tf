provider "aws" {
  alias  = "primary"
  region = var.aws_region_primary
}

provider "aws" {
  alias  = "secondary"
  region = var.aws_region_secondary
}
