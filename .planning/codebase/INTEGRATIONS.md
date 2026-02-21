# External Integrations

**Analysis Date:** 2026-02-20

## APIs & External Services

**Telegram:**
- Telegram Bot API - Primary user interface for message delivery and interaction
  - SDK/Client: Python Telegram Bot (inferred from code structure)
  - Auth: `TELEGRAM_BOT_TOKEN` environment variable in `docker-compose.yml` line 31
  - Endpoints used: `/sendChatAction`, `/sendMessage` (in `/Users/waltervargas-pena/Documents/chatbotAI/multi_personality_bot.py` lines 337, 347)
  - Deep linking supported for trial signup flow (`https://t.me/intimateaibot?start=trial` pattern in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_ARCHITECTURE.md` line 223)

**Stripe:**
- Stripe Payment Processing - Monthly subscription management and payment collection
  - SDK/Client: stripe Python SDK
  - Auth: `STRIPE_SECRET_KEY` for API calls, `STRIPE_WEBHOOK_SECRET` for webhook verification (both in `docker-compose.yml` lines 23-24)
  - Webhook endpoint: `/api/webhooks/` configured in `nginx/nginx.conf` lines 155-166
  - Features: Customer creation, subscription management, payment links, webhook event handling
  - Events tracked: `invoice.payment_succeeded`, `invoice.payment_failed` (referenced in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` lines 74-79)
  - Subscription tiers: basic ($29.99), premium ($49.99), couples ($69.99) monthly

**OpenAI (Optional):**
- OpenAI API - External LLM integration (optional feature)
  - SDK/Client: openai Python SDK
  - Auth: `OPENAI_API_KEY` environment variable in `docker-compose.yml` line 32
  - Status: Optional integration for advanced features

## Data Storage

**Databases:**

**PostgreSQL (Primary Data Store):**
- Provider: Railway.app (free 500MB tier) or DigitalOcean managed
- Connection: `DATABASE_URL` environment variable in `docker-compose.yml` line 19
- Client: SQLAlchemy ORM (inferred from FastAPI architecture pattern)
- Tables managed: users, subscriptions, usage_sessions, user_personalities, payment_events
- Schema documented in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` lines 108-149
- Backup configuration: Automatic backups with 30-day retention in Terraform
- High availability: 2 replicas in production via `terraform/main.tf` lines 50-52
- Maintenance window: Sunday at 4 AM UTC (configurable)

**Redis (Caching & Sessions):**
- Provider: Upstash (free 10K requests/day tier) or DigitalOcean managed
- Connection: `REDIS_URL` environment variable in `docker-compose.yml` line 20
- Client: redis-py (inferred)
- Purpose: Session caching, rate limiting, background job queue
- Connection limits: 10 connections max for startup (cost optimization in `docker-compose.yml` line 45)
- Production sizing: db-s-1vcpu-2gb in Terraform `terraform/main.tf` line 53

**File Storage:**
- Local filesystem initially at `/app/uploads` mounted as Docker volume in `docker-compose.yml` line 49
- Future migration: DigitalOcean Spaces (S3-compatible object storage)
- Spaces credentials: Optional via `DO_SPACES_ACCESS_ID` and `DO_SPACES_SECRET_KEY` in Terraform variables

**Caching:**
- Redis via Upstash for free tier
- Rate limiting states stored in Redis
- Session data caching

## Authentication & Identity

**Auth Provider:**
- Custom JWT-based authentication
  - Implementation: JWT tokens signed with `JWT_SECRET_KEY` (in `docker-compose.yml` line 27)
  - Method: Bearer token authentication for API endpoints
  - User identification: Telegram user ID as primary identifier in database

**Telegram Integration:**
- User identity source: Telegram user IDs (BIGINT in database schema)
- Email collection: Optional during trial signup flow
- No OAuth implementation; direct Telegram authentication

## Monitoring & Observability

**Error Tracking:**
- Not detected in codebase
- Recommended: Sentry integration (mentioned in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` line 308)

**Logs:**
- Standard approach: Python logging module with LOG_LEVEL configuration (in `docker-compose.yml` line 39)
- Log destinations: `/app/logs` Docker volume (line 48)
- Nginx access/error logs: `/var/log/nginx/` (line 76)
- Structured logging patterns in `/Users/waltervargas-pena/Documents/chatbotAI/multi_personality_bot.py` lines 27-28

**Uptime Monitoring:**
- DigitalOcean uptime monitoring via Terraform module at `terraform/modules/monitoring/`
- Health check endpoint: `/api/health` (referenced in `docker-compose.yml` lines 52 and `nginx/nginx.conf` line 169)
- Check frequency: 30 seconds with 10-second timeout
- Alert destinations: Email (configured via `alert_email` Terraform variable) and Slack webhooks

## CI/CD & Deployment

**Hosting:**
- DigitalOcean (primary platform)
- DigitalOcean App Platform for managed containerized deployment (production)
- DigitalOcean Droplets for startup ($12/month, 1GB RAM) via Docker Compose
- Alternative: Vercel/Netlify for landing page frontend (mentioned in documentation)

**CI Pipeline:**
- GitHub integration configured in Terraform: `github_repo = "epiphanyapps/chatbotAI"` (`terraform/main.tf` line 127)
- Branch-based deployments: main → production, develop → staging (`terraform/main.tf` line 128)
- Automated deployments through DigitalOcean App Platform

**Container Registry:**
- Docker images built from Dockerfile in backend directory
- Local multi-stage builds for production optimization

## Environment Configuration

**Required env vars (Critical):**
- `TELEGRAM_BOT_TOKEN` - Telegram bot authentication
- `STRIPE_SECRET_KEY` - Payment processing authentication
- `JWT_SECRET_KEY` - Authentication token signing
- `ENCRYPTION_KEY` - Data encryption at rest
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis cache connection
- `DO_TOKEN` - DigitalOcean API token (Terraform only)

**Optional env vars:**
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification
- `OPENAI_API_KEY` - External LLM features
- `TELEGRAM_BOT_TOKEN` - For premium Telegram integration

**Secrets location:**
- Docker Compose: Environment variables passed at runtime (never committed)
- Terraform: `terraform.tfvars` files (marked sensitive, not committed)
- DigitalOcean: Secrets managed via App Platform environment variables UI
- Local development: `.env` file (in `.gitignore`)

## Webhooks & Callbacks

**Incoming:**

**Stripe Webhooks:**
- Endpoint: `/api/webhooks/` (nginx/nginx.conf lines 155-166)
- Events handled:
  - `invoice.payment_succeeded` - Activate user subscription
  - `invoice.payment_failed` - Suspend access / send retry notification
  - `customer.subscription.deleted` - Cleanup on cancellation
- Signature verification: Using `STRIPE_WEBHOOK_SECRET`
- Request body limit: 1M (line 165 nginx.conf)
- No rate limiting applied (webhook-specific, line 156)

**Outgoing:**
- Telegram message delivery via Telegram Bot API (not traditional webhooks)
- Email notifications (framework not yet integrated, planned in technical implementation)
- Referral tracking webhooks (planned feature)

## Third-Party Integrations

**Landing Page Platforms (Planned):**
- Vercel or Netlify - Frontend hosting with automatic deployments
- Google Analytics - User behavior tracking
- Mixpanel - Event analytics and funnel tracking (referenced in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` lines 288-302)
- ConvertKit or Mailchimp - Email marketing integration

**Domain & DNS:**
- Domain registrar: GoDaddy/Namecheap for intimateai.chat
- DNS provider: Cloudflare (mentioned for CDN in technical docs)
- SSL certificates: Let's Encrypt (certbot container in `docker-compose.yml` lines 93-111)
- Auto-renewal: Certbot renewal every 12 hours

**Legal & Compliance:**
- Age verification: 18+ checkbox on signup (mentioned in `/Users/waltervargas-pena/Documents/chatbotAI/SAAS_TECHNICAL_IMPLEMENTATION.md` line 276)
- GDPR compliance flags in Terraform (`gdpr_compliance` variable, `terraform/variables.tf` line 275)
- Stripe adult content merchant classification

---

*Integration audit: 2026-02-20*
