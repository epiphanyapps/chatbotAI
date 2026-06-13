# ChatbotAI App Platform Module
# Managed application deployment on DigitalOcean App Platform
# Note: App Platform app creation is deferred until application code exists

terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
  }
}

#==============================================================================
# APP PLATFORM APPLICATION
#==============================================================================
# Note: The full App Platform app is deferred until frontend/backend code exists.
# This creates a placeholder app spec that can be updated when code is ready.

# App Platform application
# The app exists and will be updated when code is deployed
# For now it's a placeholder with deployment intentionally allowed to fail
resource "digitalocean_app" "chatbotai" {
  spec {
    name   = var.name_prefix
    region = var.region

    # Static site placeholder - will be replaced with actual app via CI/CD
    # Using inline HTML to avoid build failures
    static_site {
      name           = "placeholder"
      build_command  = "echo 'Placeholder'"
      output_dir     = "."
      index_document = "index.html"

      # Use a sample repo that always succeeds
      git {
        repo_clone_url = "https://github.com/digitalocean/sample-html.git"
        branch         = "main"
      }

      # Environment variables
      env {
        key   = "NODE_ENV"
        value = var.environment
      }
    }
  }

  lifecycle {
    # Ignore changes to spec as app will be updated via CI/CD
    ignore_changes = [
      spec
    ]
  }
}

#==============================================================================
# OUTPUTS FOR DATABASE CONNECTIONS
#==============================================================================
# These will be populated by the database module and used by App Platform
# when the full application is deployed
