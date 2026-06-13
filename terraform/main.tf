# ChatbotAI Infrastructure - Main Configuration
# Adult AI SaaS Platform on DigitalOcean

terraform {
  required_version = ">= 1.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  # Terraform Cloud remote state (locking + history + secret-aware storage).
  # Organization comes from TF_CLOUD_ORGANIZATION and the workspace from
  # TF_WORKSPACE, so the same config serves every environment. For local dev,
  # drop a gitignored `*_override.tf` with a local backend.
  cloud {}
}

# DigitalOcean Provider
provider "digitalocean" {
  token = var.do_token
}

# Local variables
locals {
  name_prefix = "chatbotai-${var.environment}"

  common_tags = {
    Environment = var.environment
    Project     = "ChatbotAI"
    ManagedBy   = "terraform"
    Purpose     = "adult-ai-saas"
  }

  # Database configurations per environment
  db_config = {
    dev = {
      postgres_size  = "db-s-1vcpu-1gb"
      postgres_nodes = 1
      redis_size     = "db-s-1vcpu-1gb"
      redis_nodes    = 1
    }
    staging = {
      postgres_size  = "db-s-1vcpu-2gb"
      postgres_nodes = 1
      redis_size     = "db-s-1vcpu-1gb"
      redis_nodes    = 1
    }
    production = {
      postgres_size  = "db-s-2vcpu-4gb"
      postgres_nodes = 2 # High availability
      redis_size     = "db-s-1vcpu-2gb"
      redis_nodes    = 1
    }
  }

  # App Platform configurations
  app_config = {
    dev = {
      web_instances = 1
      web_size      = "basic-xxs"
      api_instances = 1
      api_size      = "basic-xs"
    }
    staging = {
      web_instances = 1
      web_size      = "basic-xs"
      api_instances = 2
      api_size      = "basic-s"
    }
    production = {
      web_instances = 2
      web_size      = "basic-s"
      api_instances = 3
      api_size      = "basic-m"
    }
  }
}

#==============================================================================
# NETWORKING
#==============================================================================

module "networking" {
  source = "./modules/networking"

  environment = var.environment
  region      = var.region
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

#==============================================================================
# DATABASES
#==============================================================================

module "database" {
  source = "./modules/database"

  environment = var.environment
  region      = var.region
  name_prefix = local.name_prefix
  vpc_uuid    = module.networking.vpc_id
  tags        = local.common_tags

  # PostgreSQL configuration
  postgres_size  = local.db_config[var.environment].postgres_size
  postgres_nodes = local.db_config[var.environment].postgres_nodes

  # Valkey (Redis-compatible) configuration
  redis_size  = local.db_config[var.environment].redis_size
  redis_nodes = local.db_config[var.environment].redis_nodes
}

#==============================================================================
# APPLICATION PLATFORM
#==============================================================================

module "app_platform" {
  source = "./modules/app-platform"

  environment = var.environment
  name_prefix = local.name_prefix
  region      = var.region

  # GitHub configuration
  github_repo   = "epiphanyapps/chatbotAI"
  github_branch = "main" # Only main branch exists currently

  # Domain configuration
  domain_name = var.environment == "production" ? "intimateai.chat" : "${var.environment}.intimateai.chat"

  # Scaling configuration
  web_instance_count = local.app_config[var.environment].web_instances
  web_instance_size  = local.app_config[var.environment].web_size
  api_instance_count = local.app_config[var.environment].api_instances
  api_instance_size  = local.app_config[var.environment].api_size

  # Database connections
  postgres_connection_uri = module.database.postgres_private_uri
  redis_connection_uri    = module.database.redis_private_uri

  # Environment variables
  stripe_secret_key  = var.stripe_secret_key
  telegram_bot_token = var.telegram_bot_token
  jwt_secret_key     = var.jwt_secret_key
  openrouter_api_key = var.openrouter_api_key
  encryption_key     = var.encryption_key

  depends_on = [
    module.database
  ]
}

#==============================================================================
# DATABASE FIREWALLS (trusted sources)
#==============================================================================
# Managed databases expose a PUBLIC connection endpoint by default; private
# networking alone does not close it. These firewalls restrict both clusters to
# the App Platform app (plus optional admin IPs). They live at the root rather
# than inside the database module to break the db -> app dependency cycle: the
# database is created first, the app second, and the firewall (needing both
# cluster ids and the app id) last.

resource "digitalocean_database_firewall" "postgres" {
  cluster_id = module.database.postgres_id

  rule {
    type  = "app"
    value = module.app_platform.app_id
  }

  dynamic "rule" {
    for_each = var.allowed_admin_ips
    content {
      type  = "ip_addr"
      value = rule.value
    }
  }
}

resource "digitalocean_database_firewall" "redis" {
  cluster_id = module.database.redis_id

  rule {
    type  = "app"
    value = module.app_platform.app_id
  }

  dynamic "rule" {
    for_each = var.allowed_admin_ips
    content {
      type  = "ip_addr"
      value = rule.value
    }
  }
}

#==============================================================================
# MONITORING & OBSERVABILITY
#==============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment
  name_prefix = local.name_prefix
  region      = var.region

  # Application URLs for uptime monitoring
  app_url = module.app_platform.app_url
  api_url = "${module.app_platform.app_url}/api"

  # Notification settings
  alert_email   = var.alert_email
  slack_webhook = var.slack_webhook

  depends_on = [
    module.app_platform
  ]
}