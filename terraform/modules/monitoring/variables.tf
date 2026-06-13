# Monitoring Module Variables

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

variable "app_url" {
  description = "Main application URL to monitor"
  type        = string
}

variable "api_url" {
  description = "API endpoint URL to monitor"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "slack_webhook" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}

variable "uptime_regions" {
  description = "Regions for uptime monitoring"
  type        = list(string)
  # Valid DigitalOcean uptime check regions: us_east, us_west, eu_west, se_asia
  default = ["us_east", "us_west", "eu_west"]

  validation {
    condition = alltrue([
      for region in var.uptime_regions : contains([
        "us_east", "us_west", "eu_west", "se_asia"
      ], region)
    ])
    error_message = "Invalid uptime monitoring region. Valid: us_east, us_west, eu_west, se_asia"
  }
}

variable "response_time_threshold" {
  description = "Response time alert threshold in milliseconds"
  type        = number
  default     = 5000

  validation {
    condition     = var.response_time_threshold >= 100 && var.response_time_threshold <= 30000
    error_message = "Response time threshold must be between 100ms and 30s."
  }
}

variable "enable_compliance_monitoring" {
  description = "Enable adult content compliance monitoring"
  type        = bool
  default     = true
}

variable "external_webhook_urls" {
  description = "External webhook URLs for monitoring integrations"
  type        = list(string)
  default     = []
}

variable "export_monitoring_config" {
  description = "Export monitoring configuration to JSON file"
  type        = bool
  default     = false
}