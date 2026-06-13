# ChatbotAI Production Environment Configuration

#==============================================================================
# BASIC CONFIGURATION
#==============================================================================

environment = "production"
region      = "nyc3"

#==============================================================================
# DOMAIN CONFIGURATION
#==============================================================================

domain_name = "intimateai.chat"

#==============================================================================
# SCALING CONFIGURATION
#==============================================================================

# Database scaling for production load
postgres_backup_hour      = 3 # 3 AM UTC
postgres_backup_minute    = 0
database_maintenance_hour = 4 # 4 AM UTC Sunday
database_maintenance_day  = "sunday"

# Enable production features
enable_autoscaling            = false # Start with manual scaling
enable_monitoring             = true
enable_point_in_time_recovery = true
backup_retention_days         = 30
enable_audit_logging          = true

#==============================================================================
# SECURITY CONFIGURATION
#==============================================================================

force_https     = true
enable_waf      = false # DigitalOcean doesn't have native WAF
enable_cdn      = true
gdpr_compliance = true

# IP restrictions (empty list allows all - configure for production)
allowed_ips = []

#==============================================================================
# MONITORING & ALERTING
#==============================================================================

uptime_check_regions     = ["us_east", "us_west", "eu_central"]
enable_scheduled_scaling = false
log_level                = "INFO"

# Cost optimization
night_mode_schedule = "0 2 * * *" # 2 AM UTC - scale down
day_mode_schedule   = "0 8 * * *" # 8 AM UTC - scale up

#==============================================================================
# COMPLIANCE & LEGAL
#==============================================================================

data_residency_region = "us"
enable_debug_mode     = false

#==============================================================================
# PERFORMANCE TUNING
#==============================================================================

max_scale_instances = 5

#==============================================================================
# ENVIRONMENT VARIABLES (SECRETS MANAGED SEPARATELY)
#==============================================================================

# These should be set via environment variables or Terraform Cloud:
# - do_token
# - stripe_secret_key
# - jwt_secret_key
# - telegram_bot_token (optional)
# - openrouter_api_key (conversation engine)
# - encryption_key
# - alert_email
# - slack_webhook (optional)