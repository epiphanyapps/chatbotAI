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
# LOAD BALANCER
#==============================================================================
# NOTE: No DigitalOcean Load Balancer is provisioned. This is an App Platform
# (managed/serverless) deployment — App Platform fronts the app with its own
# managed ingress/TLS and has no droplets for a LB to target. The previous
# `digitalocean_loadbalancer` here targeted droplet port 8000 with no backends,
# so it routed nowhere while still billing. If the deployment ever moves to
# Droplets, reintroduce a load balancer with explicit droplet targets.

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
  # App Platform serves traffic via its managed ingress. Prefer a CNAME to the
  # app's *.ondigitalocean.app host in real DNS; this A record is a fallback for
  # an explicit fronting IP (e.g. a reserved IP) when one is provided.
  value = var.app_platform_ip
  ttl   = 3600
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
# The load-balancer CPU alert was removed along with the orphaned load
# balancer. App Platform exposes its own metrics/alerts; wire those via the
# monitoring module instead.