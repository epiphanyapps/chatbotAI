# Database Module Variables

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
}

variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "vpc_uuid" {
  description = "VPC UUID for private networking"
  type        = string
}

variable "tags" {
  description = "Common tags for resources"
  type        = map(string)
  default     = {}
}

#==============================================================================
# POSTGRESQL CONFIGURATION
#==============================================================================

variable "postgres_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15"
}

variable "postgres_size" {
  description = "PostgreSQL instance size"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "postgres_nodes" {
  description = "Number of PostgreSQL nodes"
  type        = number
  default     = 1
}

variable "postgres_database_name" {
  description = "Main database name"
  type        = string
  default     = "chatbotai"
}

variable "postgres_username" {
  description = "PostgreSQL application username"
  type        = string
  default     = "chatbotai_user"
}

variable "connection_pool_size" {
  description = "Size of main connection pool"
  type        = number
  default     = 10 # Reduced for smallest DB tier (25 max connections)
}

variable "readonly_pool_size" {
  description = "Size of read-only connection pool"
  type        = number
  default     = 5 # Reduced for smallest DB tier
}

variable "enable_read_replica" {
  description = "Enable read replica for production"
  type        = bool
  default     = false
}

#==============================================================================
# REDIS CONFIGURATION
#==============================================================================

variable "redis_region" {
  description = "Region for Redis cluster (some regions don't support Redis)"
  type        = string
  default     = "" # Empty means use main region
}

variable "redis_version" {
  description = "Redis version"
  type        = string
  default     = "7"
}

variable "redis_size" {
  description = "Redis instance size"
  type        = string
  default     = "db-s-1vcpu-1gb"
}

variable "redis_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1
}

#==============================================================================
# MAINTENANCE & BACKUP
#==============================================================================

variable "maintenance_day" {
  description = "Preferred maintenance day"
  type        = string
  default     = "sunday"

  validation {
    condition = contains([
      "monday", "tuesday", "wednesday", "thursday",
      "friday", "saturday", "sunday"
    ], var.maintenance_day)
    error_message = "Must be a valid day of the week."
  }
}

variable "maintenance_hour" {
  description = "Preferred maintenance hour (0-23)"
  type        = string
  default     = "04:00"
}

variable "backup_hour" {
  description = "Hour for automated backups (0-23)"
  type        = number
  default     = 2

  validation {
    condition     = var.backup_hour >= 0 && var.backup_hour <= 23
    error_message = "Backup hour must be between 0 and 23."
  }
}

variable "backup_minute" {
  description = "Minute for automated backups (0-59)"
  type        = number
  default     = 0

  validation {
    condition     = var.backup_minute >= 0 && var.backup_minute <= 59
    error_message = "Backup minute must be between 0 and 59."
  }
}

#==============================================================================
# SECURITY & ACCESS
#==============================================================================

variable "enable_ssl" {
  description = "Enable SSL for database connections"
  type        = bool
  default     = true
}

#==============================================================================
# MONITORING & ALERTING
#==============================================================================

variable "enable_monitoring" {
  description = "Enable database monitoring and alerting"
  type        = bool
  default     = true
}

variable "alert_emails" {
  description = "Email addresses for database alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for database alerts"
  type        = string
  default     = ""
}

variable "cpu_alert_threshold" {
  description = "CPU usage alert threshold (percentage)"
  type        = number
  default     = 80

  validation {
    condition     = var.cpu_alert_threshold >= 0 && var.cpu_alert_threshold <= 100
    error_message = "CPU threshold must be between 0 and 100."
  }
}

variable "memory_alert_threshold" {
  description = "Memory usage alert threshold (percentage)"
  type        = number
  default     = 85

  validation {
    condition     = var.memory_alert_threshold >= 0 && var.memory_alert_threshold <= 100
    error_message = "Memory threshold must be between 0 and 100."
  }
}

#==============================================================================
# PERFORMANCE TUNING
#==============================================================================

variable "enable_performance_insights" {
  description = "Enable performance insights (if available)"
  type        = bool
  default     = false
}

variable "query_timeout" {
  description = "Query timeout in seconds"
  type        = number
  default     = 30
}

variable "connection_timeout" {
  description = "Connection timeout in seconds"
  type        = number
  default     = 10
}

#==============================================================================
# COMPLIANCE & DATA RETENTION
#==============================================================================

variable "enable_audit_logging" {
  description = "Enable audit logging for compliance"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain database logs"
  type        = number
  default     = 30

  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 365
    error_message = "Log retention must be between 1 and 365 days."
  }
}

variable "enable_encryption_at_rest" {
  description = "Enable encryption at rest"
  type        = bool
  default     = true
}