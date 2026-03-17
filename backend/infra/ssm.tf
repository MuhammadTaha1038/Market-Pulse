# SSM Parameter Store for Oracle Database Credentials
# These will be manually populated by the DevOps/Admin team

resource "aws_ssm_parameter" "oracle_host" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/host"
  description = "Oracle database host/endpoint"
  type        = "String"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-host"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

resource "aws_ssm_parameter" "oracle_port" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/port"
  description = "Oracle database port"
  type        = "String"
  value       = "1521"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-port"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

resource "aws_ssm_parameter" "oracle_service_name" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/service_name"
  description = "Oracle database service name or SID"
  type        = "String"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-service-name"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

resource "aws_ssm_parameter" "oracle_username" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/username"
  description = "Oracle database admin username"
  type        = "SecureString"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-username"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

resource "aws_ssm_parameter" "oracle_password" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/password"
  description = "Oracle database admin password"
  type        = "SecureString"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-password"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

# Optional: Schema/Table parameters for data extraction
resource "aws_ssm_parameter" "oracle_schema" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/schema"
  description = "Oracle database schema name"
  type        = "String"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-schema"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

resource "aws_ssm_parameter" "oracle_table_name" {
  name        = "/${var.app_prefix}/${var.env}/${var.app_name}/oracle/table_name"
  description = "Oracle main table name for color data"
  type        = "String"
  value       = "PLACEHOLDER_TO_BE_UPDATED"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.app_prefix}-${var.env}-oracle-table-name"
    }
  )

  lifecycle {
    ignore_changes = [value]
  }

  provider = aws.primary
}

# Output SSM parameter names for easy reference
output "ssm_parameter_names" {
  description = "SSM Parameter names for Oracle database credentials"
  value = {
    host         = aws_ssm_parameter.oracle_host.name
    port         = aws_ssm_parameter.oracle_port.name
    service_name = aws_ssm_parameter.oracle_service_name.name
    username     = aws_ssm_parameter.oracle_username.name
    password     = aws_ssm_parameter.oracle_password.name
    schema       = aws_ssm_parameter.oracle_schema.name
    table_name   = aws_ssm_parameter.oracle_table_name.name
  }
}
