# ChatbotAI Infrastructure Outputs

#==============================================================================
# APPLICATION URLS
#==============================================================================

output "app_url" {
  description = "Main application URL"
  value       = module.app_platform.app_url
}

output "api_url" {
  description = "API endpoint URL"
  value       = "${module.app_platform.app_url}/api"
}

output "admin_url" {
  description = "Admin dashboard URL"
  value       = "${module.app_platform.app_url}/admin"
}

#==============================================================================
# NETWORKING INFORMATION
#==============================================================================

output "vpc_id" {
  description = "VPC ID for the environment"
  value       = module.networking.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.networking.vpc_cidr
}

output "region" {
  description = "Deployment region"
  value       = var.region
}

#==============================================================================
# DATABASE CONNECTION INFORMATION
#==============================================================================

output "postgres_host" {
  description = "PostgreSQL host (private network)"
  value       = module.database.postgres_host
  sensitive   = true
}

output "postgres_port" {
  description = "PostgreSQL port"
  value       = module.database.postgres_port
}

output "postgres_database" {
  description = "PostgreSQL database name"
  value       = module.database.postgres_database
}

output "postgres_username" {
  description = "PostgreSQL username"
  value       = module.database.postgres_username
  sensitive   = true
}

output "redis_host" {
  description = "Redis host (private network)"
  value       = module.database.redis_host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.database.redis_port
}

#==============================================================================
# SSL & SECURITY
#==============================================================================

output "force_https_enabled" {
  description = "HTTPS enforcement status"
  value       = var.force_https
}

#==============================================================================
# MONITORING ENDPOINTS
#==============================================================================

output "health_check_url" {
  description = "Application health check endpoint"
  value       = "${module.app_platform.app_url}/api/health"
}

output "metrics_url" {
  description = "Application metrics endpoint (if enabled)"
  value       = "${module.app_platform.app_url}/api/metrics"
}

output "uptime_check_ids" {
  description = "Uptime monitoring check IDs"
  value       = module.monitoring.uptime_check_ids
}

#==============================================================================
# APP PLATFORM DETAILS
#==============================================================================

output "app_platform_id" {
  description = "DigitalOcean App Platform application ID"
  value       = module.app_platform.app_id
}

output "app_platform_urn" {
  description = "App Platform URN for API references"
  value       = module.app_platform.app_urn
}

output "deployment_url" {
  description = "Live deployment URL from App Platform"
  value       = module.app_platform.live_url
}

#==============================================================================
# SCALING INFORMATION
#==============================================================================

output "web_instance_count" {
  description = "Current web frontend instance count"
  value       = local.app_config[var.environment].web_instances
}

output "api_instance_count" {
  description = "Current API backend instance count"
  value       = local.app_config[var.environment].api_instances
}

output "database_node_count" {
  description = "Current database node count"
  value       = local.db_config[var.environment].postgres_nodes
}

#==============================================================================
# COST INFORMATION
#==============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly infrastructure cost (USD)"
  value = {
    database = {
      postgres = local.db_config[var.environment].postgres_size
      redis    = local.db_config[var.environment].redis_size
    }
    app_platform = {
      web_tier = local.app_config[var.environment].web_size
      api_tier = local.app_config[var.environment].api_size
    }
    environment = var.environment
    note = "Actual costs may vary based on usage and scaling"
  }
}

#==============================================================================
# CONFIGURATION SUMMARY
#==============================================================================

output "deployment_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    environment     = var.environment
    region         = var.region
    app_url        = module.app_platform.app_url
    database_tier  = local.db_config[var.environment].postgres_size
    app_tier       = local.app_config[var.environment].api_size
    ssl_enabled    = true
    monitoring     = var.enable_monitoring
    backup_enabled = true
    deployed_at    = timestamp()
  }
}

#==============================================================================
# SECRETS & SENSITIVE DATA (for CI/CD)
#==============================================================================

output "database_connection_string" {
  description = "Full database connection string for application"
  value       = module.database.postgres_connection_string
  sensitive   = true
}

output "redis_connection_string" {
  description = "Redis connection string for application"
  value       = module.database.redis_connection_string
  sensitive   = true
}

#==============================================================================
# TERRAFORM STATE INFORMATION
#==============================================================================

output "terraform_workspace" {
  description = "Current Terraform workspace"
  value       = terraform.workspace
}

output "last_updated" {
  description = "Timestamp of last Terraform apply"
  value       = timestamp()
}

#==============================================================================
# DEBUGGING INFORMATION
#==============================================================================

output "debug_info" {
  description = "Debug information (dev/staging only)"
  value = var.environment != "production" ? {
    vpc_details = {
      id   = module.networking.vpc_id
      cidr = module.networking.vpc_cidr
    }
    database_details = {
      postgres_nodes = local.db_config[var.environment].postgres_nodes
      redis_nodes   = local.db_config[var.environment].redis_nodes
    }
    app_details = {
      github_repo   = "epiphanyapps/chatbotAI"
      github_branch = var.environment == "production" ? "main" : "develop"
    }
  } : null
}

#==============================================================================
# ADMIN INFORMATION
#==============================================================================

output "admin_access" {
  description = "Admin access information"
  value = {
    database_admin_url = "https://cloud.digitalocean.com/databases/${module.database.postgres_id}"
    app_platform_url   = "https://cloud.digitalocean.com/apps/${module.app_platform.app_id}"
    monitoring_url     = var.enable_monitoring ? "https://cloud.digitalocean.com/monitoring" : null
    note              = "Access requires DigitalOcean account permissions"
  }
  sensitive = true
}

#==============================================================================
# ENVIRONMENT-SPECIFIC OUTPUTS
#==============================================================================

output "environment_config" {
  description = "Environment-specific configuration details"
  value = {
    name = var.environment
    is_production = var.environment == "production"
    domain = var.environment == "production" ? "intimateai.chat" : "${var.environment}.intimateai.chat"
    features = {
      autoscaling        = var.enable_autoscaling
      monitoring        = var.enable_monitoring
      audit_logging     = var.enable_audit_logging
      gdpr_compliance   = var.gdpr_compliance
      point_in_time_recovery = var.enable_point_in_time_recovery
    }
  }
}