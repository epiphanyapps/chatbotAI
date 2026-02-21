# Database Module Outputs

#==============================================================================
# POSTGRESQL OUTPUTS
#==============================================================================

output "postgres_id" {
  description = "PostgreSQL cluster ID"
  value       = digitalocean_database_cluster.postgres.id
}

output "postgres_host" {
  description = "PostgreSQL host (private network)"
  value       = digitalocean_database_cluster.postgres.private_host
  sensitive   = true
}

output "postgres_port" {
  description = "PostgreSQL port"
  value       = digitalocean_database_cluster.postgres.port
}

output "postgres_database" {
  description = "PostgreSQL database name"
  value       = digitalocean_database_db.chatbotai.name
}

output "postgres_username" {
  description = "PostgreSQL main username"
  value       = digitalocean_database_user.chatbotai.name
  sensitive   = true
}

output "postgres_password" {
  description = "PostgreSQL main user password"
  value       = digitalocean_database_user.chatbotai.password
  sensitive   = true
}

output "postgres_private_uri" {
  description = "PostgreSQL private connection URI"
  value       = digitalocean_database_cluster.postgres.private_uri
  sensitive   = true
}

output "postgres_connection_string" {
  description = "PostgreSQL connection string for applications"
  value = format(
    "postgresql://%s:%s@%s:%s/%s?sslmode=require",
    digitalocean_database_user.chatbotai.name,
    digitalocean_database_user.chatbotai.password,
    digitalocean_database_cluster.postgres.private_host,
    digitalocean_database_cluster.postgres.port,
    digitalocean_database_db.chatbotai.name
  )
  sensitive = true
}

# Connection pool outputs
output "postgres_pool_uri" {
  description = "PostgreSQL connection pool URI"
  value       = digitalocean_database_connection_pool.chatbotai.private_uri
  sensitive   = true
}

output "postgres_readonly_pool_uri" {
  description = "PostgreSQL read-only pool URI"
  value       = length(digitalocean_database_connection_pool.readonly) > 0 ? digitalocean_database_connection_pool.readonly[0].private_uri : null
  sensitive   = true
}

# Read replica outputs (if enabled)
output "postgres_read_replica_host" {
  description = "PostgreSQL read replica host (if enabled)"
  value = length(digitalocean_database_replica.postgres_read) > 0 ? digitalocean_database_replica.postgres_read[0].private_host : null
  sensitive = true
}

output "postgres_read_replica_uri" {
  description = "PostgreSQL read replica URI (if enabled)"
  value = length(digitalocean_database_replica.postgres_read) > 0 ? digitalocean_database_replica.postgres_read[0].private_uri : null
  sensitive = true
}

#==============================================================================
# REDIS OUTPUTS
#==============================================================================

output "redis_id" {
  description = "Redis cluster ID"
  value       = digitalocean_database_cluster.redis.id
}

output "redis_host" {
  description = "Redis host (private network)"
  value       = digitalocean_database_cluster.redis.private_host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = digitalocean_database_cluster.redis.port
}

output "redis_password" {
  description = "Redis password"
  value       = digitalocean_database_cluster.redis.password
  sensitive   = true
}

output "redis_private_uri" {
  description = "Redis private connection URI"
  value       = digitalocean_database_cluster.redis.private_uri
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string for applications"
  value = format(
    "redis://:%s@%s:%s/0",
    digitalocean_database_cluster.redis.password,
    digitalocean_database_cluster.redis.private_host,
    digitalocean_database_cluster.redis.port
  )
  sensitive = true
}

#==============================================================================
# DATABASE USER OUTPUTS
#==============================================================================

output "app_write_user" {
  description = "Application write user details"
  value = {
    name     = digitalocean_database_user.app_write.name
    password = digitalocean_database_user.app_write.password
  }
  sensitive = true
}

output "readonly_user" {
  description = "Read-only user details"
  value = {
    name     = digitalocean_database_user.readonly.name
    password = digitalocean_database_user.readonly.password
  }
  sensitive = true
}

output "analytics_user" {
  description = "Analytics user details"
  value = {
    name     = digitalocean_database_user.analytics.name
    password = digitalocean_database_user.analytics.password
  }
  sensitive = true
}

output "backup_user" {
  description = "Backup user details"
  value = {
    name     = digitalocean_database_user.backup.name
    password = digitalocean_database_user.backup.password
  }
  sensitive = true
}

#==============================================================================
# CONNECTION INFORMATION
#==============================================================================

output "database_info" {
  description = "Complete database connection information"
  value = {
    postgres = {
      host             = digitalocean_database_cluster.postgres.private_host
      port             = digitalocean_database_cluster.postgres.port
      database         = digitalocean_database_db.chatbotai.name
      ssl_required     = true
      connection_pool  = digitalocean_database_connection_pool.chatbotai.name
      readonly_pool    = length(digitalocean_database_connection_pool.readonly) > 0 ? digitalocean_database_connection_pool.readonly[0].name : null
    }
    redis = {
      host        = digitalocean_database_cluster.redis.private_host
      port        = digitalocean_database_cluster.redis.port
      ssl_enabled = true
    }
  }
  sensitive = true
}

#==============================================================================
# MONITORING & STATUS
#==============================================================================

output "database_status" {
  description = "Database cluster status information"
  value = {
    postgres = {
      version    = digitalocean_database_cluster.postgres.version
      nodes      = digitalocean_database_cluster.postgres.node_count
      size       = digitalocean_database_cluster.postgres.size
      region     = digitalocean_database_cluster.postgres.region
    }
    redis = {
      version    = digitalocean_database_cluster.redis.version
      nodes      = digitalocean_database_cluster.redis.node_count
      size       = digitalocean_database_cluster.redis.size
      region     = digitalocean_database_cluster.redis.region
    }
  }
}

#==============================================================================
# BACKUP & MAINTENANCE
#==============================================================================

output "maintenance_windows" {
  description = "Database maintenance window information"
  value = {
    postgres = {
      day  = digitalocean_database_cluster.postgres.maintenance_window[0].day
      hour = digitalocean_database_cluster.postgres.maintenance_window[0].hour
    }
    redis = {
      day  = digitalocean_database_cluster.redis.maintenance_window[0].day
      hour = digitalocean_database_cluster.redis.maintenance_window[0].hour
    }
  }
}

#==============================================================================
# ADMINISTRATIVE ACCESS
#==============================================================================

output "admin_access" {
  description = "Administrative access information"
  value = {
    postgres_console = "https://cloud.digitalocean.com/databases/${digitalocean_database_cluster.postgres.id}"
    redis_console    = "https://cloud.digitalocean.com/databases/${digitalocean_database_cluster.redis.id}"
    monitoring_url   = var.enable_monitoring ? "https://cloud.digitalocean.com/monitoring" : null
  }
}

#==============================================================================
# COST INFORMATION
#==============================================================================

output "estimated_cost" {
  description = "Estimated monthly database costs"
  value = {
    postgres = {
      size  = var.postgres_size
      nodes = var.postgres_nodes
      note  = "PostgreSQL main cluster"
    }
    redis = {
      size  = var.redis_size
      nodes = var.redis_nodes
      note  = "Redis cache cluster"
    }
    replica = length(digitalocean_database_replica.postgres_read) > 0 ? {
      size = var.postgres_size
      note = "PostgreSQL read replica"
    } : null
    total_note = "Actual costs may vary based on usage and data transfer"
  }
}