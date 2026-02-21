# ChatbotAI Monitoring Module
# Uptime monitoring, alerts, and observability
# Simplified for initial deployment

terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

#==============================================================================
# UPTIME MONITORING
#==============================================================================

resource "digitalocean_uptime_check" "web_app" {
  name    = "${var.name_prefix}-web-uptime"
  target  = var.app_url
  type    = "https"
  regions = var.uptime_regions
  enabled = true
}

resource "digitalocean_uptime_check" "api_health" {
  name    = "${var.name_prefix}-api-health"
  target  = var.api_url
  type    = "https"
  regions = var.uptime_regions
  enabled = true
}

#==============================================================================
# UPTIME ALERTS
#==============================================================================

resource "digitalocean_uptime_alert" "web_app_down" {
  check_id = digitalocean_uptime_check.web_app.id
  name     = "${var.name_prefix}-web-down-alert"
  type     = "down"

  notifications {
    email = var.alert_email != "" ? [var.alert_email] : []

    dynamic "slack" {
      for_each = var.slack_webhook != "" ? [1] : []
      content {
        channel = "#infrastructure-alerts"
        url     = var.slack_webhook
      }
    }
  }

  comparison = "less_than"
  threshold  = 1
  period     = "2m"
}

resource "digitalocean_uptime_alert" "api_health_down" {
  check_id = digitalocean_uptime_check.api_health.id
  name     = "${var.name_prefix}-api-health-down"
  type     = "down"

  notifications {
    email = var.alert_email != "" ? [var.alert_email] : []

    dynamic "slack" {
      for_each = var.slack_webhook != "" ? [1] : []
      content {
        channel = "#api-alerts"
        url     = var.slack_webhook
      }
    }
  }

  comparison = "less_than"
  threshold  = 1
  period     = "2m"
}

# SSL certificate expiration alert
resource "digitalocean_uptime_alert" "ssl_expiry" {
  check_id = digitalocean_uptime_check.web_app.id
  name     = "${var.name_prefix}-ssl-expiry-alert"
  type     = "ssl_expiry"

  notifications {
    email = var.alert_email != "" ? [var.alert_email] : []

    dynamic "slack" {
      for_each = var.slack_webhook != "" ? [1] : []
      content {
        channel = "#security-alerts"
        url     = var.slack_webhook
      }
    }
  }

  # Alert 30 days before SSL expiry
  comparison = "less_than"
  threshold  = 30
  period     = "30m"  # Valid period value
}
