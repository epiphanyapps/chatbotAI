# ChatbotAI Networking Module
# VPC and networking infrastructure

terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

#==============================================================================
# VPC (VIRTUAL PRIVATE CLOUD)
#==============================================================================

resource "digitalocean_vpc" "main" {
  name     = "${var.name_prefix}-vpc"
  region   = var.region
  ip_range = var.vpc_cidr
  
  description = "Private network for ChatbotAI ${var.environment} environment"
}

#==============================================================================
# FIREWALL RULES
#==============================================================================

# NOTE: DigitalOcean Firewalls only apply to Droplets, not App Platform.
# Since we're using App Platform (managed/serverless), firewall rules are handled
# automatically by DigitalOcean. Database firewalls are configured separately
# via digitalocean_database_firewall resources.
#
# These firewall resources are disabled for App Platform deployments.
# Re-enable if switching to Droplet-based deployment.

# resource "digitalocean_firewall" "web" {
#   name = "${var.name_prefix}-web-fw"
#   # ... firewall rules for Droplet-based deployments
# }

# resource "digitalocean_firewall" "database" {
#   name = "${var.name_prefix}-db-fw"
#   # ... firewall rules for Droplet-based deployments
# }

#==============================================================================
# LOAD BALANCER (if needed for high availability)
#==============================================================================

# Create load balancer for production environment
resource "digitalocean_loadbalancer" "main" {
  count = var.environment == "production" ? 1 : 0
  
  name     = "${var.name_prefix}-lb"
  region   = var.region
  vpc_uuid = digitalocean_vpc.main.id
  
  # HTTPS forwarding rule
  forwarding_rule {
    entry_protocol  = "https"
    entry_port      = 443
    target_protocol = "http"
    target_port     = 8000
    certificate_name = var.ssl_certificate_name != "" ? var.ssl_certificate_name : null
    tls_passthrough = false
  }
  
  # HTTP forwarding rule (redirect to HTTPS)
  forwarding_rule {
    entry_protocol  = "http"
    entry_port      = 80
    target_protocol = "http"
    target_port     = 8000
  }
  
  # Health check configuration
  healthcheck {
    protocol               = "http"
    port                   = 8000
    path                   = "/api/health"
    check_interval_seconds = 10
    response_timeout_seconds = 5
    unhealthy_threshold    = 3
    healthy_threshold      = 2
  }
  
  # Sticky sessions for adult content (user preference continuity)
  sticky_sessions {
    type               = "cookies"
    cookie_name        = "chatbotai_session"
    cookie_ttl_seconds = 3600
  }
  
  # Enable PROXY protocol for real IP addresses
  enable_proxy_protocol = true
  
  # Security: Disable HTTP/2 for better control (optional)
  disable_lets_encrypt_dns_records = false
}

#==============================================================================
# DOMAIN RECORDS (if managing DNS through DigitalOcean)
#==============================================================================

# Only create domain records if managing DNS through DO
resource "digitalocean_domain" "main" {
  count = var.manage_dns ? 1 : 0
  
  name = var.domain_name
}

# A record pointing to load balancer or app platform
resource "digitalocean_record" "main" {
  count = var.manage_dns ? 1 : 0
  
  domain = digitalocean_domain.main[0].name
  type   = "A"
  name   = var.environment == "production" ? "@" : var.environment
  value  = var.environment == "production" && length(digitalocean_loadbalancer.main) > 0 ? digitalocean_loadbalancer.main[0].ip : var.app_platform_ip
  ttl    = 3600
}

# CNAME for www subdomain
resource "digitalocean_record" "www" {
  count = var.manage_dns && var.environment == "production" ? 1 : 0
  
  domain = digitalocean_domain.main[0].name
  type   = "CNAME" 
  name   = "www"
  value  = "${digitalocean_domain.main[0].name}."
  ttl    = 3600
}

# CNAME for API subdomain
resource "digitalocean_record" "api" {
  count = var.manage_dns ? 1 : 0
  
  domain = digitalocean_domain.main[0].name
  type   = "CNAME"
  name   = "api"
  value  = var.environment == "production" ? "${digitalocean_domain.main[0].name}." : "${var.environment}.${digitalocean_domain.main[0].name}."
  ttl    = 3600
}

#==============================================================================
# RESERVED IP (for production stability)
#==============================================================================

resource "digitalocean_reserved_ip" "main" {
  count  = var.environment == "production" ? 1 : 0
  region = var.region
}

#==============================================================================
# MONITORING ENDPOINTS
#==============================================================================

# Create monitoring checks for network endpoints
resource "digitalocean_monitor_alert" "load_balancer_health" {
  count = var.environment == "production" && length(digitalocean_loadbalancer.main) > 0 ? 1 : 0

  alerts {
    email = [var.alert_email]
    slack {
      channel = "#infrastructure-alerts"
      url     = var.slack_webhook_url
    }
  }

  window      = "5m"
  type        = "v1/insights/lbaas/avg_cpu_utilization_percent"
  compare     = "GreaterThan"
  value       = 80
  enabled     = true
  entities    = [digitalocean_loadbalancer.main[0].id]
  description = "${var.environment} load balancer CPU utilization"
}