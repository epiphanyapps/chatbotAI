# ChatbotAI Infrastructure Variables

#==============================================================================
# ENVIRONMENT & BASIC CONFIG
#==============================================================================

variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "region" {
  description = "DigitalOcean region for resources"
  type        = string
  default     = "nyc3"

  validation {
    condition = contains([
      "nyc1", "nyc3", "ams3", "sfo3", "sgp1", "lon1",
      "fra1", "tor1", "blr1", "syd1"
    ], var.region)
    error_message = "Must be a valid DigitalOcean region."
  }
}

#==============================================================================
# DIGITALOCEAN CREDENTIALS
#==============================================================================

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "do_spaces_access_id" {
  description = "DigitalOcean Spaces access key ID (for backups)"
  type        = string
  default     = ""
}

variable "do_spaces_secret_key" {
  description = "DigitalOcean Spaces secret access key"
  type        = string
  sensitive   = true
  default     = ""
}

#==============================================================================
# APPLICATION SECRETS
#==============================================================================

variable "stripe_secret_key" {
  description = "Stripe secret key for payment processing (Phase 4 — optional until then)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook endpoint secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "telegram_bot_token" {
  description = "Telegram bot API token (for premium feature)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for the conversation engine"
  type        = string
  sensitive   = true
  default     = ""
}

variable "encryption_key" {
  description = "Application encryption key for sensitive data"
  type        = string
  sensitive   = true
}

#==============================================================================
# DOMAIN & SSL
#==============================================================================

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "intimateai.chat"
}

variable "subdomain_prefix" {
  description = "Subdomain prefix for non-production environments"
  type        = string
  default     = ""
}

#==============================================================================
# DATABASE CONFIGURATION
#==============================================================================

variable "postgres_backup_hour" {
  description = "Hour of day for PostgreSQL backups (0-23)"
  type        = number
  default     = 2 # 2 AM UTC

  validation {
    condition     = var.postgres_backup_hour >= 0 && var.postgres_backup_hour <= 23
    error_message = "Backup hour must be between 0 and 23."
  }
}

variable "postgres_backup_minute" {
  description = "Minute of hour for PostgreSQL backups (0-59)"
  type        = number
  default     = 0

  validation {
    condition     = var.postgres_backup_minute >= 0 && var.postgres_backup_minute <= 59
    error_message = "Backup minute must be between 0 and 59."
  }
}

variable "database_maintenance_hour" {
  description = "Preferred hour for database maintenance (0-23)"
  type        = number
  default     = 4 # 4 AM UTC
}

variable "database_maintenance_day" {
  description = "Preferred day for database maintenance"
  type        = string
  default     = "sunday"

  validation {
    condition = contains([
      "monday", "tuesday", "wednesday", "thursday",
      "friday", "saturday", "sunday"
    ], var.database_maintenance_day)
    error_message = "Must be a valid day of the week."
  }
}

#==============================================================================
# MONITORING & ALERTING
#==============================================================================

variable "alert_email" {
  description = "Email address for infrastructure alerts"
  type        = string
  default     = ""
}

variable "slack_webhook" {
  description = "Slack webhook URL for notifications"
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring and alerting"
  type        = bool
  default     = true
}

variable "uptime_check_regions" {
  description = "Regions for uptime monitoring"
  type        = list(string)
  default     = ["us_east", "us_west", "eu_central"]
}

#==============================================================================
# SCALING & PERFORMANCE
#==============================================================================

variable "enable_autoscaling" {
  description = "Enable App Platform autoscaling"
  type        = bool
  default     = false # Start with manual scaling
}

variable "max_scale_instances" {
  description = "Maximum number of instances for autoscaling"
  type        = number
  default     = 5
}

variable "enable_cdn" {
  description = "Enable CDN for static assets"
  type        = bool
  default     = true
}

#==============================================================================
# SECURITY CONFIGURATION
#==============================================================================

variable "allowed_ips" {
  description = "IP addresses allowed to access admin endpoints"
  type        = list(string)
  default     = [] # Empty list allows all IPs
}

variable "allowed_admin_ips" {
  description = "IP addresses granted direct (admin/debug) access to the managed databases, in addition to the App Platform app. Empty = app-only."
  type        = list(string)
  default     = []
}

variable "enable_waf" {
  description = "Enable Web Application Firewall (if available)"
  type        = bool
  default     = false # DigitalOcean doesn't have native WAF yet
}

variable "force_https" {
  description = "Force HTTPS redirects"
  type        = bool
  default     = true
}

#==============================================================================
# BACKUP & DISASTER RECOVERY
#==============================================================================

variable "backup_retention_days" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 1 and 365 days."
  }
}

variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for PostgreSQL"
  type        = bool
  default     = false # Enable for production
}

#==============================================================================
# COMPLIANCE & LEGAL
#==============================================================================

variable "enable_audit_logging" {
  description = "Enable comprehensive audit logging"
  type        = bool
  default     = true
}

variable "data_residency_region" {
  description = "Ensure data residency in specific region for compliance"
  type        = string
  default     = "us"

  validation {
    condition     = contains(["us", "eu", "asia"], var.data_residency_region)
    error_message = "Data residency must be: us, eu, or asia."
  }
}

variable "gdpr_compliance" {
  description = "Enable GDPR compliance features"
  type        = bool
  default     = true
}

#==============================================================================
# DEVELOPMENT & TESTING
#==============================================================================

variable "enable_debug_mode" {
  description = "Enable debug mode (dev/staging only)"
  type        = bool
  default     = false
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARN", "ERROR"], var.log_level)
    error_message = "Log level must be: DEBUG, INFO, WARN, or ERROR."
  }
}

#==============================================================================
# COST OPTIMIZATION
#==============================================================================

variable "enable_scheduled_scaling" {
  description = "Enable scheduled scaling for cost optimization"
  type        = bool
  default     = false
}

variable "night_mode_schedule" {
  description = "Cron schedule for night mode scaling (reduce instances)"
  type        = string
  default     = "0 2 * * *" # 2 AM UTC
}

variable "day_mode_schedule" {
  description = "Cron schedule for day mode scaling (restore instances)"
  type        = string
  default     = "0 8 * * *" # 8 AM UTC
}