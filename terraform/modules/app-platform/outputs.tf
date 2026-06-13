# App Platform Module Outputs

#==============================================================================
# APPLICATION URLS
#==============================================================================

output "app_id" {
  description = "App Platform application ID"
  value       = digitalocean_app.chatbotai.id
}

output "app_urn" {
  description = "App Platform application URN"
  value       = digitalocean_app.chatbotai.urn
}

output "app_url" {
  description = "Main application URL"
  value       = "https://${var.domain_name}"
}

output "live_url" {
  description = "Live deployment URL from App Platform"
  value       = digitalocean_app.chatbotai.live_url
}

output "default_ingress" {
  description = "Default App Platform ingress URL"
  value       = digitalocean_app.chatbotai.default_ingress
}

#==============================================================================
# APPLICATION CONFIGURATION
#==============================================================================

output "app_configuration" {
  description = "Application configuration summary"
  value = {
    name        = var.name_prefix
    environment = var.environment
    region      = var.region
    domain      = var.domain_name
    github_repo = var.github_repo
  }
}

#==============================================================================
# DEPLOYMENT INFORMATION
#==============================================================================

output "deployment_info" {
  description = "Deployment information"
  value = {
    app_platform_console = "https://cloud.digitalocean.com/apps/${digitalocean_app.chatbotai.id}"
    live_url             = digitalocean_app.chatbotai.live_url
    custom_domain        = var.domain_name
    created_at           = digitalocean_app.chatbotai.created_at
    updated_at           = digitalocean_app.chatbotai.updated_at
  }
}
