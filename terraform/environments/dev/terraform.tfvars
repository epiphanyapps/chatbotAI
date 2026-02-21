# ChatbotAI Development Environment Configuration

#==============================================================================
# BASIC CONFIGURATION
#==============================================================================

environment = "dev"
region      = "nyc3"

#==============================================================================
# DOMAIN CONFIGURATION
#==============================================================================

domain_name = "dev.intimateai.chat"

#==============================================================================
# COST OPTIMIZATION FOR DEV
#==============================================================================

# Smaller instances for development
postgres_backup_hour   = 4
postgres_backup_minute = 0
database_maintenance_hour = 5
database_maintenance_day  = "sunday"

# Disable expensive features for dev
enable_autoscaling             = false
enable_monitoring             = true   # Keep monitoring for testing
enable_point_in_time_recovery = false  # Not needed for dev
backup_retention_days         = 7      # Shorter retention
enable_audit_logging          = false  # Reduce costs

#==============================================================================
# SECURITY CONFIGURATION (RELAXED FOR DEV)
#==============================================================================

force_https     = true
enable_waf      = false
enable_cdn      = false  # Not needed for dev
gdpr_compliance = true   # Test compliance features

# Allow all IPs for development
allowed_ips = []

#==============================================================================
# MONITORING & ALERTING
#==============================================================================

uptime_check_regions     = ["us_east"]  # Single region for dev
enable_scheduled_scaling = false
log_level               = "DEBUG"       # Verbose logging for dev

#==============================================================================
# COMPLIANCE & LEGAL
#==============================================================================

data_residency_region = "us"
enable_debug_mode     = true  # Enable debug features

#==============================================================================
# PERFORMANCE TUNING
#==============================================================================

max_scale_instances = 2  # Limit scaling for dev

#==============================================================================
# ENVIRONMENT VARIABLES (SECRETS MANAGED SEPARATELY)
#==============================================================================

# For development, these can be set locally or via .env files:
# - do_token (required)
# - stripe_secret_key (test keys)
# - jwt_secret_key (test secret)
# - telegram_bot_token (test bot - optional)
# - openai_api_key (optional)
# - encryption_key (test key)
# - alert_email (developer email)
# - slack_webhook (optional)