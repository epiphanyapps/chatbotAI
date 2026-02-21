# Phase 1 Research: Infrastructure Deployment

**Phase Goal:** Deploy Terraform infrastructure to DigitalOcean with databases and monitoring
**Researched:** 2026-02-21

## Executive Summary

Phase 1 involves deploying **already-implemented Terraform code** (GitHub Issue #12 marked COMPLETE) to DigitalOcean. The infrastructure code exists in `terraform/` with modules for networking, databases, app platform, and monitoring. This is a deployment/configuration phase, not a coding phase.

The primary work involves:
1. DigitalOcean account setup and API token creation
2. GitHub secrets configuration
3. Terraform state backend configuration
4. Initial dev environment deployment
5. Validation of deployed resources

## Existing Infrastructure Analysis

### Terraform Structure (Complete)
```
terraform/
├── main.tf                    # Root module - orchestrates all modules
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── modules/
│   ├── networking/            # VPC, firewall, load balancer
│   ├── database/              # PostgreSQL + Redis managed DBs
│   ├── app-platform/          # DigitalOcean App Platform config
│   └── monitoring/            # Uptime checks, alerting
└── environments/
    ├── dev/terraform.tfvars   # Dev config (~$150/mo)
    └── production/terraform.tfvars  # Prod config (~$400/mo)
```

### CI/CD Pipeline (Complete)
- `.github/workflows/terraform-deploy.yml` exists
- Auto-deploys on push to main (production) or develop (dev)
- Security scanning with Checkov and tfsec
- Slack notifications

### Required GitHub Secrets
```
DO_TOKEN              # DigitalOcean API token (REQUIRED)
STRIPE_SECRET_KEY     # Stripe API key (can use test key initially)
STRIPE_WEBHOOK_SECRET # Stripe webhook secret (configure after deployment)
JWT_SECRET_KEY        # Generate: openssl rand -hex 32
TELEGRAM_BOT_TOKEN    # Existing bot token (optional for Phase 1)
OPENAI_API_KEY        # Not used - using local Ollama
ENCRYPTION_KEY        # Generate: openssl rand -hex 32
ALERT_EMAIL           # Email for infrastructure alerts
SLACK_WEBHOOK         # Slack webhook URL (optional)
TF_API_TOKEN          # Terraform Cloud token (optional)
```

## Prerequisites Verification

### Must Have Before Deployment
| Prerequisite | Status | Required For |
|--------------|--------|--------------|
| DigitalOcean account | Not verified | All resources |
| DO API token (write access) | Not verified | Terraform provider |
| Domain IntimateAI.chat | Not purchased | DNS/SSL |
| GitHub repo access | Exists | CI/CD deployment |
| Stripe account | Not started | App env vars |

### Nice to Have (Can Configure Later)
- Slack webhook for notifications
- Terraform Cloud account for state management
- Custom alerting email

## Deployment Strategy

### Recommended Approach: Dev First
1. **Deploy Dev Environment** - Lower cost, test configuration
2. **Validate Resources** - Check databases, app platform, monitoring
3. **Configure Secrets** - Set up GitHub repository secrets
4. **Test CI/CD** - Push change to develop branch, verify auto-deploy
5. **Document Access** - Save connection strings, URLs

### Cost Estimate
- **Dev environment**: ~$150/month
  - PostgreSQL (1 node): ~$60
  - Redis (1 node): ~$15
  - App Platform: ~$50
  - Storage/Monitoring: ~$25

### Manual vs CI/CD Deployment
**Recommendation: Manual first deployment**

The CI/CD workflow requires:
- Backend state configured (Terraform Cloud or S3)
- All secrets in GitHub
- Working Terraform Cloud token

For initial deployment, manual `terraform apply` is simpler:
1. Set environment variables locally
2. Run `terraform init && terraform plan`
3. Review plan output
4. Run `terraform apply`

After initial deployment, enable CI/CD for subsequent changes.

## Technical Considerations

### State Backend
The `main.tf` configures remote backend for Terraform Cloud:
```hcl
backend "remote" {
  # Terraform Cloud for state management
}
```

**Options:**
1. **Terraform Cloud (Free tier)** - Create workspace, set TF_API_TOKEN
2. **DigitalOcean Spaces** - S3-compatible backend (add ~$5/mo)
3. **Local state** - Not recommended for team/CI but works for initial setup

### Database Connections
After deployment, connection strings available via:
```bash
terraform output postgres_private_uri
terraform output redis_private_uri
```

These are VPC-private URIs, accessible only from within DigitalOcean network.

### SSL/HTTPS
- App Platform provides automatic Let's Encrypt certificates
- Domain must point to App Platform URL first
- SSL provisioning happens after DNS propagation (up to 24h)

### Monitoring Setup
The monitoring module creates:
- Uptime checks for web and API endpoints
- SSL certificate expiration alerts
- Email notifications via `alert_email` variable

## Gaps and Blockers

### Critical Blockers
1. **Domain not purchased** - Cannot configure SSL or production DNS
   - Action: Purchase IntimateAI.chat before Phase 5 (Landing Page)
   - Not blocking for Phase 1 dev deployment

2. **DigitalOcean account status unknown** - Need API token
   - Action: Create account or retrieve existing token

### Non-Blocking Gaps
1. **Terraform Cloud not configured** - Can use local state initially
2. **Slack notifications** - Optional, can add later
3. **Stripe keys** - Can use test keys; not needed until Phase 4

## Success Criteria Mapping

| Roadmap Success Criteria | How to Verify |
|-------------------------|---------------|
| Terraform applies successfully | `terraform apply` exits 0 |
| PostgreSQL accepts connections | `terraform output postgres_private_uri` + test connection |
| Redis accepts connections | `terraform output redis_private_uri` + test connection |
| SSL certificates auto-renew | Check App Platform console (after DNS setup) |
| Uptime monitoring triggers | Test `/health` endpoint down scenario |

## Recommended Plan Structure

### Plan A: Manual Dev Deployment
**Complexity:** Low | **Duration:** Single session

Steps:
1. Verify/create DigitalOcean API token
2. Generate JWT and encryption secrets
3. Create Terraform workspace (dev)
4. Run terraform init with local backend (temporarily)
5. Run terraform plan with dev.tfvars
6. Review plan output
7. Run terraform apply
8. Verify resources in DO console
9. Test database connectivity
10. Configure GitHub secrets for CI/CD

### Plan B: Full CI/CD Setup
**Complexity:** Medium | **Duration:** Multiple sessions

Additional steps:
1. Create Terraform Cloud account/workspace
2. Configure state backend
3. Set all GitHub secrets
4. Push to develop branch
5. Verify GitHub Actions workflow runs

**Recommendation:** Start with Plan A (manual), enable CI/CD after validation.

---
*Research complete. Ready for plan creation.*
