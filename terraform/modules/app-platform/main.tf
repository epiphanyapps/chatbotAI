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
# Two components on one app, fronted by App Platform ingress:
#   - api: FastAPI backend (built from backend/Dockerfile), served at /api
#   - web: React/Vite static SPA, served at /
# Requires a DigitalOcean <-> GitHub OAuth connection so App Platform can build
# from the repo. Secrets are injected as SECRET-type env vars (encrypted at rest).
resource "digitalocean_app" "chatbotai" {
  spec {
    name   = var.name_prefix
    region = var.region

    # ---- API: FastAPI backend ------------------------------------------------
    service {
      name               = "api"
      instance_count     = var.api_instance_count
      instance_size_slug = var.api_instance_size
      http_port          = 8080

      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = var.github_auto_deploy
      }
      source_dir      = "backend"
      dockerfile_path = "backend/Dockerfile"

      health_check {
        http_path = "/health"
      }

      # Connection strings (the app normalises the driver/SSL itself).
      env {
        key   = "DATABASE_URL"
        value = var.postgres_connection_uri
        type  = "SECRET"
      }
      env {
        key   = "DATABASE_SSL_CA"
        value = var.postgres_ca_cert
        type  = "SECRET"
      }
      env {
        key   = "VALKEY_URL"
        value = var.redis_connection_uri
        type  = "SECRET"
      }
      env {
        key   = "VALKEY_SSL_CA"
        value = var.redis_ca_cert
        type  = "SECRET"
      }
      env {
        key   = "JWT_SECRET"
        value = var.jwt_secret_key
        type  = "SECRET"
      }
      env {
        key   = "MAGIC_LINK_SECRET"
        value = var.magic_link_secret
        type  = "SECRET"
      }
      env {
        key   = "RESEND_API_KEY"
        value = var.resend_api_key
        type  = "SECRET"
      }
      env {
        key   = "OPENROUTER_API_KEY"
        value = var.openrouter_api_key
        type  = "SECRET"
      }
      env {
        key   = "APP_URL"
        value = "https://${var.domain_name}"
      }
      env {
        key   = "ENVIRONMENT"
        value = var.environment
      }
      env {
        key   = "DEBUG"
        value = "false"
      }
    }

    # ---- WEB: React/Vite SPA (static) ---------------------------------------
    static_site {
      name              = "web"
      build_command     = "npm ci && npm run build"
      output_dir        = "dist"
      catchall_document = "index.html" # client-side routing fallback

      github {
        repo           = var.github_repo
        branch         = var.github_branch
        deploy_on_push = var.github_auto_deploy
      }
      source_dir = "frontend"
    }

    # ---- Ingress: /api -> api (prefix stripped), everything else -> web ------
    ingress {
      rule {
        component {
          name                 = "api"
          preserve_path_prefix = false # backend sees /auth, /chat, /health
        }
        match {
          path {
            prefix = "/api"
          }
        }
      }
      rule {
        component {
          name = "web"
        }
        match {
          path {
            prefix = "/"
          }
        }
      }
    }
  }
}

#==============================================================================
# OUTPUTS FOR DATABASE CONNECTIONS
#==============================================================================
# These will be populated by the database module and used by App Platform
# when the full application is deployed
