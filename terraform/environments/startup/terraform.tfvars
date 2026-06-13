# ChatbotAI Startup Environment - Ultra Cost Optimized
# Target: <$30/month until you have paying users

#==============================================================================
# BASIC CONFIGURATION
#==============================================================================

environment = "startup"
region      = "nyc3"

#==============================================================================
# DOMAIN CONFIGURATION
#==============================================================================

domain_name = "startup.intimateai.chat" # Subdomain initially

#==============================================================================
# ULTRA COST OPTIMIZATION
#==============================================================================

# Smallest possible database sizes
postgres_size  = "db-s-1vcpu-1gb" # $15/month
postgres_nodes = 1                # Single node only
redis_size     = "db-s-1vcpu-1gb" # $15/month  
redis_nodes    = 1

# Minimal app instances
web_instance_count    = 1
web_instance_size     = "basic-xxs" # $5/month
api_instance_count    = 1
api_instance_size     = "basic-xxs" # $5/month
worker_instance_count = 0           # No background workers initially

# Disable expensive features
enable_autoscaling            = false
enable_monitoring             = false # Save $5-10/month initially
enable_point_in_time_recovery = false
enable_read_replica           = false
backup_retention_days         = 7 # Minimal backups
enable_audit_logging          = false
enable_cdn                    = false # Save CDN costs

#==============================================================================
# SIMPLIFIED SECURITY (BASIC)
#==============================================================================

force_https     = true
enable_waf      = false
gdpr_compliance = true

#==============================================================================
# MINIMAL MONITORING
#==============================================================================

uptime_check_regions     = ["us_east"] # Single region
enable_scheduled_scaling = false
log_level                = "INFO"

#==============================================================================
# STARTUP MODE FEATURES
#==============================================================================

data_residency_region = "us"
enable_debug_mode     = false
max_scale_instances   = 2

#==============================================================================
# COST TARGETS
#==============================================================================

# Target monthly costs:
# - PostgreSQL: $15/month (smallest instance)
# - Redis: $15/month (smallest instance)
# - App Platform: $10/month (2x basic-xxs instances)
# - Storage: $2/month (minimal usage)
# - SSL: Free (Let's Encrypt)
# - Monitoring: $0 (basic only)
# Total: ~$42/month
#
# Break-even: 2 subscribers at $29.99 = $59.98 MRR
# Profit margin: $17.98/month with 2 users