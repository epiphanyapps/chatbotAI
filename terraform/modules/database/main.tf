# ChatbotAI Database Module
# Managed PostgreSQL and Redis clusters

terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

#==============================================================================
# POSTGRESQL DATABASE CLUSTER
#==============================================================================

resource "digitalocean_database_cluster" "postgres" {
  name       = "${var.name_prefix}-postgres"
  engine     = "pg"
  version    = var.postgres_version
  size       = var.postgres_size
  region     = var.region
  node_count = var.postgres_nodes

  # Private networking for security
  private_network_uuid = var.vpc_uuid

  # Maintenance window (low-traffic hours)
  maintenance_window {
    day  = var.maintenance_day
    hour = var.maintenance_hour
  }

  # Note: Automatic daily backups are included with managed databases
  # 7-day retention by default

  tags = concat(
    [var.environment, "database", "postgres", "chatbotai"],
    [for k, v in var.tags : "${k}:${v}"]
  )
}

# Create application database
resource "digitalocean_database_db" "chatbotai" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.postgres_database_name
}

# Create application database user
resource "digitalocean_database_user" "chatbotai" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = var.postgres_username
}

# Create read-only user for analytics/reporting
resource "digitalocean_database_user" "readonly" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "${var.postgres_username}_readonly"
}

#==============================================================================
# VALKEY CLUSTER (for sessions, caching, rate limiting)
# NOTE: DigitalOcean replaced Redis with Valkey (Redis-compatible fork)
#==============================================================================

resource "digitalocean_database_cluster" "redis" {
  name       = "${var.name_prefix}-valkey"
  engine     = "valkey"
  version    = "8" # Valkey only supports version 8
  size       = var.redis_size
  region     = var.region
  node_count = var.redis_nodes

  # Private networking
  private_network_uuid = var.vpc_uuid

  # Maintenance window (same as PostgreSQL)
  maintenance_window {
    day  = var.maintenance_day
    hour = var.maintenance_hour
  }

  # Note: redis_config is configured via DigitalOcean dashboard or API
  # Default configuration uses allkeys-lru eviction policy

  tags = concat(
    [var.environment, "cache", "redis", "chatbotai"],
    [for k, v in var.tags : "${k}:${v}"]
  )
}

#==============================================================================
# DATABASE CONNECTION POOLS (for better performance)
#==============================================================================

resource "digitalocean_database_connection_pool" "chatbotai" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "${var.postgres_database_name}_pool"
  mode       = "transaction" # Good for web applications
  size       = var.connection_pool_size
  db_name    = digitalocean_database_db.chatbotai.name
  user       = digitalocean_database_user.chatbotai.name
}

# Read-only connection pool for analytics
# Disabled for dev environment (smallest DB tier has limited connections)
resource "digitalocean_database_connection_pool" "readonly" {
  count      = var.environment != "dev" ? 1 : 0
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "${var.postgres_database_name}_readonly_pool"
  mode       = "session" # Better for analytics queries
  size       = var.readonly_pool_size
  db_name    = digitalocean_database_db.chatbotai.name
  user       = digitalocean_database_user.readonly.name
}

#==============================================================================
# DATABASE REPLICAS (for production read scaling)
#==============================================================================

resource "digitalocean_database_replica" "postgres_read" {
  count = var.environment == "production" && var.enable_read_replica ? 1 : 0

  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "${var.name_prefix}-postgres-read"
  region     = var.region
  size       = var.postgres_size

  private_network_uuid = var.vpc_uuid

  tags = concat(
    [var.environment, "database", "postgres-replica", "chatbotai"],
    [for k, v in var.tags : "${k}:${v}"]
  )
}

#==============================================================================
# DATABASE FIREWALL RULES
#==============================================================================

# Trusted-source firewalls are defined at the ROOT module
# (digitalocean_database_firewall.postgres / .redis in ../../main.tf) so they
# can reference the App Platform app id without creating a db -> app dependency
# cycle. Cluster ids are exported via outputs.tf for that wiring.

#==============================================================================
# DATABASE MONITORING
#==============================================================================

# NOTE: digitalocean_monitor_alert for database alerts is temporarily disabled
# due to a bug in terraform-provider-digitalocean v2.76.0 that causes a panic
# when creating alerts. Re-enable when provider is fixed.
# See: https://github.com/digitalocean/terraform-provider-digitalocean/issues
#
# For now, configure database alerts manually via DigitalOcean dashboard:
# - PostgreSQL CPU > 80%
# - PostgreSQL Memory > 85%
# - Redis Memory > 90%

# resource "digitalocean_monitor_alert" "postgres_cpu" {
#   count = var.enable_monitoring ? 1 : 0
#   ...
# }

# resource "digitalocean_monitor_alert" "postgres_memory" {
#   count = var.enable_monitoring ? 1 : 0
#   ...
# }

# resource "digitalocean_monitor_alert" "redis_memory" {
#   count = var.enable_monitoring ? 1 : 0
#   ...
# }

#==============================================================================
# BACKUP CONFIGURATION
#==============================================================================

# Note: DigitalOcean managed databases include automatic daily backups
# Manual backup snapshots can be triggered via API or dashboard
# Backup retention is 7 days by default

# NOTE: Previously this module also created `_write`, `_analytics`, and
# `_backup` users. They had no grants and nothing consumed them, so they were
# removed to avoid unused privileged credentials. Re-add (with explicit, scoped
# permissions) if/when a real consumer exists. The `_readonly` user remains —
# it backs the read-only connection pool above.