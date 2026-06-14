# App Platform Module Variables

#==============================================================================
# BASIC CONFIGURATION
#==============================================================================

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

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

#==============================================================================
# GITHUB INTEGRATION
#==============================================================================

variable "github_repo" {
  description = "GitHub repository in format owner/repo"
  type        = string
}

variable "github_branch" {
  description = "GitHub branch to deploy from"
  type        = string
  default     = "main"
}

variable "github_auto_deploy" {
  description = "Enable auto-deployment on push"
  type        = bool
  default     = true
}

#==============================================================================
# SCALING CONFIGURATION
#==============================================================================

variable "web_instance_count" {
  description = "Number of web frontend instances"
  type        = number
  default     = 1

  validation {
    condition     = var.web_instance_count >= 1 && var.web_instance_count <= 10
    error_message = "Web instance count must be between 1 and 10."
  }
}

variable "web_instance_size" {
  description = "Size of web frontend instances"
  type        = string
  default     = "basic-xxs"

  validation {
    condition = contains([
      "basic-xxs", "basic-xs", "basic-s", "basic-m",
      "professional-xs", "professional-s", "professional-m", "professional-l"
    ], var.web_instance_size)
    error_message = "Must be a valid App Platform instance size."
  }
}

variable "api_instance_count" {
  description = "Number of API backend instances"
  type        = number
  default     = 1

  validation {
    condition     = var.api_instance_count >= 1 && var.api_instance_count <= 10
    error_message = "API instance count must be between 1 and 10."
  }
}

variable "api_instance_size" {
  description = "Size of API backend instances"
  type        = string
  default     = "basic-xs"

  validation {
    condition = contains([
      "basic-xxs", "basic-xs", "basic-s", "basic-m",
      "professional-xs", "professional-s", "professional-m", "professional-l"
    ], var.api_instance_size)
    error_message = "Must be a valid App Platform instance size."
  }
}

variable "worker_instance_count" {
  description = "Number of background worker instances"
  type        = number
  default     = 1
}

variable "worker_instance_size" {
  description = "Size of background worker instances"
  type        = string
  default     = "basic-xxs"
}

#==============================================================================
# DATABASE CONNECTIONS
#==============================================================================

variable "postgres_connection_uri" {
  description = "PostgreSQL connection URI"
  type        = string
  sensitive   = true
}

variable "redis_connection_uri" {
  description = "Redis connection URI"
  type        = string
  sensitive   = true
}

variable "postgres_ca_cert" {
  description = "CA certificate (PEM/base64) for verifying Postgres TLS"
  type        = string
  sensitive   = true
  default     = ""
}

variable "redis_ca_cert" {
  description = "CA certificate (PEM/base64) for verifying Valkey/Redis TLS"
  type        = string
  sensitive   = true
  default     = ""
}

variable "postgres_cluster_name" {
  description = "Name of PostgreSQL cluster for App Platform reference"
  type        = string
  default     = ""
}

#==============================================================================
# APPLICATION SECRETS
#==============================================================================

variable "stripe_secret_key" {
  description = "Stripe secret key"
  type        = string
  sensitive   = true
}

variable "stripe_publishable_key" {
  description = "Stripe publishable key"
  type        = string
  default     = ""
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Telegram bot token (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openrouter_api_key" {
  description = "OpenRouter API key for the conversation engine"
  type        = string
  sensitive   = true
  default     = ""
}

variable "magic_link_secret" {
  description = "Secret for signing passwordless magic-link tokens"
  type        = string
  sensitive   = true
  default     = ""
}

variable "resend_api_key" {
  description = "Resend API key for sending magic-link emails"
  type        = string
  sensitive   = true
  default     = ""
}

variable "encryption_key" {
  description = "Application encryption key"
  type        = string
  sensitive   = true
}

#==============================================================================
# FEATURE FLAGS
#==============================================================================

variable "enable_cdn" {
  description = "Enable CDN for static assets"
  type        = bool
  default     = true
}

variable "enable_auto_scaling" {
  description = "Enable automatic scaling"
  type        = bool
  default     = false
}

variable "enable_health_checks" {
  description = "Enable health checks"
  type        = bool
  default     = true
}

variable "enable_cors" {
  description = "Enable CORS configuration"
  type        = bool
  default     = true
}

variable "enable_ssl_redirect" {
  description = "Force HTTPS redirects"
  type        = bool
  default     = true
}

#==============================================================================
# APPLICATION CONFIGURATION
#==============================================================================

variable "trial_duration_minutes" {
  description = "Trial duration in minutes"
  type        = number
  default     = 120 # 2 hours

  validation {
    condition     = var.trial_duration_minutes > 0 && var.trial_duration_minutes <= 1440
    error_message = "Trial duration must be between 1 and 1440 minutes (24 hours)."
  }
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

variable "worker_concurrency" {
  description = "Number of concurrent workers for background tasks"
  type        = number
  default     = 2

  validation {
    condition     = var.worker_concurrency >= 1 && var.worker_concurrency <= 16
    error_message = "Worker concurrency must be between 1 and 16."
  }
}

#==============================================================================
# MONITORING & ALERTING
#==============================================================================

variable "enable_monitoring" {
  description = "Enable application monitoring"
  type        = bool
  default     = true
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

variable "response_time_threshold" {
  description = "Response time alert threshold (milliseconds)"
  type        = number
  default     = 5000

  validation {
    condition     = var.response_time_threshold >= 100 && var.response_time_threshold <= 30000
    error_message = "Response time threshold must be between 100 and 30000 milliseconds."
  }
}

variable "alert_emails" {
  description = "Email addresses for alerts"
  type        = list(string)
  default     = []
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

#==============================================================================
# STORAGE CONFIGURATION
#==============================================================================

variable "enable_file_uploads" {
  description = "Enable file upload functionality"
  type        = bool
  default     = true
}

variable "max_file_size_mb" {
  description = "Maximum file upload size in MB"
  type        = number
  default     = 10

  validation {
    condition     = var.max_file_size_mb >= 1 && var.max_file_size_mb <= 100
    error_message = "Max file size must be between 1 and 100 MB."
  }
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30

  validation {
    condition     = var.backup_retention_days >= 1 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 1 and 365 days."
  }
}

#==============================================================================
# SECURITY CONFIGURATION
#==============================================================================

variable "allowed_origins" {
  description = "Allowed CORS origins"
  type        = list(string)
  default     = []
}

variable "enable_rate_limiting" {
  description = "Enable API rate limiting"
  type        = bool
  default     = true
}

variable "rate_limit_requests_per_minute" {
  description = "API rate limit (requests per minute)"
  type        = number
  default     = 60

  validation {
    condition     = var.rate_limit_requests_per_minute >= 1 && var.rate_limit_requests_per_minute <= 1000
    error_message = "Rate limit must be between 1 and 1000 requests per minute."
  }
}

variable "enable_audit_logging" {
  description = "Enable audit logging"
  type        = bool
  default     = true
}

variable "session_timeout_minutes" {
  description = "User session timeout in minutes"
  type        = number
  default     = 60

  validation {
    condition     = var.session_timeout_minutes >= 5 && var.session_timeout_minutes <= 1440
    error_message = "Session timeout must be between 5 and 1440 minutes."
  }
}

#==============================================================================
# COMPLIANCE CONFIGURATION
#==============================================================================

variable "enable_gdpr_compliance" {
  description = "Enable GDPR compliance features"
  type        = bool
  default     = true
}

variable "data_retention_days" {
  description = "Data retention period in days"
  type        = number
  default     = 365

  validation {
    condition     = var.data_retention_days >= 30 && var.data_retention_days <= 2555 # 7 years
    error_message = "Data retention must be between 30 and 2555 days."
  }
}

variable "enable_adult_content_warnings" {
  description = "Enable adult content warnings and age verification"
  type        = bool
  default     = true
}

variable "minimum_user_age" {
  description = "Minimum user age for registration"
  type        = number
  default     = 18

  validation {
    condition     = var.minimum_user_age >= 13 && var.minimum_user_age <= 21
    error_message = "Minimum age must be between 13 and 21."
  }
}