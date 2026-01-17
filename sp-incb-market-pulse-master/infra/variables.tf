variable "aws_region_primary" {
  type        = string
  description = "Primary region where to deploy the application."
}

variable "aws_region_secondary" {
  type        = string
  description = "Secondary region where to deploy the application."
}

variable "app_prefix" {
  type = string
}

variable "app_name" {
  type = string
}

variable "vpc" {
  type        = string
  description = "VPC in which to connect the function. vpc_connectivity must be true for this to have effect."
  default     = "sp-incb"
}


variable "env" {
  type = string
}

variable "lambda_runtime" {
  type        = string
  description = "Runtime used by AWS Lambda to run the function."
  default     = "python3.11"
}

variable "lambda_handler" {
  type        = string
  description = "Handler to be called by AWS Lambda when the function is invoked. Usually defined in GitLab CI."
}

variable "lambda_memory" {
  type        = number
  description = "AWS Lambda function's memory in MB."
  default     = 1024
}

variable "lambda_timeout" {
  type        = number
  description = "AWS Lambda function execution's timeout."
  default     = 900
}

variable "lambda_pkg_s3_name" {
  type        = string
  description = "Name of the zip archive in S3 (only object name without key prefix) that contains the function's code. Usually defined in GitLab CI."
}

variable "primary_bin_bucket" {
  type        = string
  default     = ""
  description = "(Optional) S3 Bucket used for the application deployment"
}

variable "secondary_bin_bucket" {
  type        = string
  default     = ""
  description = "(Optional) S3 Bucket used for the application deployment"
}


variable "code_version" {
  type = string
}

variable "release_version" {
  type = string
}

variable "is_versioned" {
  type = string
  default = "false"
}

variable "hosted_zone_name" {
  type        = string
  description = "Check aws-lambda module documentation."
  default     = ""
}

variable "bucket_required" {
  type = string
  description = "Whether a backing bucket is required"
  default = false
}

variable "bucket_name" {
  type = string
  description = "Any customized bucket name if required"
  default = null
}
variable "user_id" {
  type = string
  default="tejas.dewan"
  description = "User who created the application"
}

variable "config_region_primary" {
  type        = string
  description = "Primary AWS Region set in the config"
  default     = ""
}
variable "config_region_secondary" {
  type        = string
  description = "Secondary AWS Region set in the config"
  default     = ""
}
variable "host_based_routing" {
  description = "If true then Host Based Routing is enabled otherwise Path Based"
  type        = bool
  default     = true
}
variable "routing_policy_type" {
  description = "Type of routing policy used by the Route 53 record"
  type        = string
  default     = "weighted"
}
variable "primary_routing_weight" {
  description = "Weight of Route 53 record in Primary Region. Used only if routing_policy_type is weighted"
  type        = number
  default     = 255
}
variable "secondary_routing_weight" {
  description = "Weight of Route 53 record in Secondary Region. Used only if routing_policy_type is weighted"
  type        = number
  default     = 0
}

variable "lambda_layer" {
  type        = string
  description = "AWS Lambda Layer (only name and version) to attach to the Lambda function. The layer must be available in all regions where the Lambda functions are deployed."
  default     = null
}

variable "dr_enabled" {
  type        = bool
  default     = true
  description = "Whether this application will have DR"  
}



