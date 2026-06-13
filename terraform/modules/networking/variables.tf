# Networking Module Variables

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

variable "tags" {
  description = "Common tags for resources"
  type        = map(string)
  default     = {}
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "allowed_ssh_ips" {
  description = "IP addresses allowed SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict in production
}

variable "ssl_certificate_name" {
  description = "Name of SSL certificate for load balancer"
  type        = string
  default     = ""
}

variable "manage_dns" {
  description = "Whether to manage DNS records through DigitalOcean"
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain name for DNS management"
  type        = string
  default     = ""
}

variable "app_platform_ip" {
  description = "App Platform IP for DNS records"
  type        = string
  default     = ""
}

variable "alert_email" {
  description = "Email for monitoring alerts"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook for alerts"
  type        = string
  default     = ""
}