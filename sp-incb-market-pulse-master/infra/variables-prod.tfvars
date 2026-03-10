env                    = "prod"
app_prefix             = "sp-incb"
app_name               = "market-pulse"
aws_region_primary     = "us-east-1"
aws_region_secondary   = "us-west-2"
lambda_handler         = "handler.app"
lambda_pkg_s3_name     = "market-pulse.zip"
code_version           = "1.0.0"
release_version        = ""
bucket_required        = true
bucket_name            = "sp-incb-prod-market-pulse"
dr_enabled             = true
# TODO: get these two bucket names from client DevOps team
primary_bin_bucket     = "REPLACE_WITH_CLIENT_BINARY_BUCKET_US_EAST_1"
secondary_bin_bucket   = "REPLACE_WITH_CLIENT_BINARY_BUCKET_US_WEST_2"
# TODO: get the Oracle credentials API URL from the client
oracle_credentials_api_url = "REPLACE_WITH_ORACLE_CREDENTIALS_API_URL"
