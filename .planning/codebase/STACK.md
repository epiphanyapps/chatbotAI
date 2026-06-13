# Technology Stack

**Analysis Date:** 2026-02-20

## Languages

**Primary:**
- Python 3 - Backend bot logic, personality system, user management
- JavaScript/Node.js - (Planned) Landing page backend if needed

**Secondary:**
- SQL - PostgreSQL database queries
- HCL - Terraform infrastructure as code

## Runtime

**Environment:**
- Docker containers (primary execution environment)
- Bare metal support (DigitalOcean droplets)

**Package Manager:**
- pip - Python dependency management
- npm - (Minimal) JavaScript tooling for infrastructure scripts

**Lockfile:**
- `requirements.txt` - Python dependencies specified in `/Users/waltervargas-pena/Documents/chatbotAI/requirements.txt`
- No package-lock or yarn.lock detected (Node.js usage is minimal)

## Frameworks

**Core:**
- FastAPI (planned, referenced in documentation) - Python async web framework for REST API endpoints on port 8000
- Telegram Bot Framework - Bot polling/webhook integration via `python-telegram-bot` or similar (inferred from code structure)

**Supporting:**
- scikit-learn - TF-IDF vectorization and cosine similarity for training data matching in `/Users/waltervargas-pena/Documents/chatbotAI/multi_personality_bot.py`
- numpy - Numerical operations for similarity calculations

**Build/Dev:**
- Docker/Docker Compose - Containerization for local development and production deployment
- Terraform ~> 2.0 - Infrastructure provisioning on DigitalOcean

## Key Dependencies

**Critical:**
- requests>=2.28.0 - HTTP client for Telegram API calls in `/Users/waltervargas-pena/Documents/chatbotAI/multi_personality_bot.py` line 8
- scikit-learn>=1.1.0 - Machine learning for TF-IDF vectorization in `/Users/waltervargas-pena/Documents/chatbotAI/multi_personality_bot.py` line 13
- numpy>=1.21.0 - Numerical computing for cosine similarity operations

**Infrastructure:**
- DigitalOcean Spaces SDK - Object storage for backups (optional, referenced in Terraform variables)
- stripe Python SDK - Payment processing and webhook handling (required for subscription system)
- cryptography - Fernet encryption for sensitive user data encryption in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` line 261

**Optional/Future:**
- transformers - Large language model support (commented out in requirements.txt)
- torch - PyTorch for advanced ML features (commented out in requirements.txt)

## Configuration

**Environment:**
Configuration via environment variables in Docker Compose (`docker-compose.yml` lines 17-40):
- `DATABASE_URL` - PostgreSQL connection string (Railway.app free tier)
- `REDIS_URL` - Redis cache connection (Upstash free tier)
- `STRIPE_SECRET_KEY` - Payment processor authentication
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification
- `JWT_SECRET_KEY` - JWT token signing for authentication
- `ENCRYPTION_KEY` - Application-level data encryption
- `TELEGRAM_BOT_TOKEN` - Telegram bot API token
- `OPENAI_API_KEY` - Optional external LLM integration
- `DOMAIN` - Primary domain (intimateai.chat)
- `TRIAL_DURATION_MINUTES` - Trial period length (120 minutes default, should be 1440 for 24 hours)
- `ENABLE_ADULT_CONTENT` - Boolean flag for content type
- `LOG_LEVEL` - Logging verbosity (INFO/DEBUG/ERROR/WARN)
- `CORS_ORIGINS` - Allowed CORS origins for web frontend
- `ENABLE_BACKGROUND_WORKERS` - Process-level worker configuration
- `MAX_CONNECTIONS` - Database connection pool limits
- `REDIS_MAX_CONNECTIONS` - Redis connection limits

**Build:**
- `docker-compose.yml` - Multi-container orchestration for API, nginx, certbot, optional worker
- Dockerfile (referenced but not provided) - Backend application containerization
- `nginx/nginx.conf` - Reverse proxy, SSL/TLS termination, rate limiting at `/Users/waltervargas-pena/Documents/chatbotAI/nginx/nginx.conf`

**Terraform Configuration:**
- `terraform/main.tf` - Infrastructure orchestration with modules for networking, database, app-platform, monitoring
- `terraform/variables.tf` - Input variables with validation for DigitalOcean resources
- `terraform/environments/*/terraform.tfvars` - Environment-specific values (dev, staging, production)

## Platform Requirements

**Development:**
- macOS/Linux/Windows with Docker installed
- Python 3.8+ for local script execution
- Terraform 1.0+ for infrastructure provisioning
- Git for version control

**Production:**
- DigitalOcean droplet (1GB RAM minimum, $12/month startup tier)
- DigitalOcean App Platform for managed containerized deployments
- DigitalOcean PostgreSQL managed database (free 500MB tier via Railway.app for startup)
- DigitalOcean Redis managed cache (free via Upstash for startup)
- Let's Encrypt SSL certificates for HTTPS/TLS

**External Services:**
- Railway.app - Free PostgreSQL hosting (500MB included)
- Upstash - Free Redis hosting (10K requests/day)
- Stripe - Payment processing (connected via API)
- Telegram - Bot platform and message delivery

---

*Stack analysis: 2026-02-20*
