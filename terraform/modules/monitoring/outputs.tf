# Monitoring Module Outputs

output "uptime_check_ids" {
  description = "List of uptime check IDs"
  value = [
    digitalocean_uptime_check.web_app.id,
    digitalocean_uptime_check.api_health.id
  ]
}

output "uptime_checks" {
  description = "Uptime check details"
  value = {
    web_app = {
      id     = digitalocean_uptime_check.web_app.id
      name   = digitalocean_uptime_check.web_app.name
      target = digitalocean_uptime_check.web_app.target
      type   = digitalocean_uptime_check.web_app.type
    }
    api_health = {
      id     = digitalocean_uptime_check.api_health.id
      name   = digitalocean_uptime_check.api_health.name
      target = digitalocean_uptime_check.api_health.target
      type   = digitalocean_uptime_check.api_health.type
    }
  }
}

output "alert_configurations" {
  description = "Alert configuration details"
  value = {
    web_down = {
      id        = digitalocean_uptime_alert.web_app_down.id
      name      = digitalocean_uptime_alert.web_app_down.name
      type      = digitalocean_uptime_alert.web_app_down.type
      threshold = digitalocean_uptime_alert.web_app_down.threshold
      period    = digitalocean_uptime_alert.web_app_down.period
    }
    api_down = {
      id        = digitalocean_uptime_alert.api_health_down.id
      name      = digitalocean_uptime_alert.api_health_down.name
      type      = digitalocean_uptime_alert.api_health_down.type
      threshold = digitalocean_uptime_alert.api_health_down.threshold
      period    = digitalocean_uptime_alert.api_health_down.period
    }
    ssl_expiry = {
      id        = digitalocean_uptime_alert.ssl_expiry.id
      name      = digitalocean_uptime_alert.ssl_expiry.name
      type      = digitalocean_uptime_alert.ssl_expiry.type
      threshold = digitalocean_uptime_alert.ssl_expiry.threshold
      period    = digitalocean_uptime_alert.ssl_expiry.period
    }
  }
}

output "monitoring_dashboard_url" {
  description = "DigitalOcean monitoring dashboard URL"
  value       = "https://cloud.digitalocean.com/monitoring"
}

output "monitoring_summary" {
  description = "Complete monitoring configuration summary"
  value = {
    environment        = var.environment
    total_checks       = 2
    alert_email        = var.alert_email != "" ? "configured" : "not configured"
    slack_webhook      = var.slack_webhook != "" ? "configured" : "not configured"
    uptime_regions     = var.uptime_regions
    response_threshold = var.response_time_threshold
  }
}
