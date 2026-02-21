# Phase 1 Plan: Infrastructure Deployment

**Phase Goal:** Deploy Terraform infrastructure to DigitalOcean with databases and monitoring
**Created:** 2026-02-21
**Approach:** Manual dev deployment first, then CI/CD enablement

## Plan Overview

This phase deploys existing Terraform infrastructure (GitHub Issue #12) to DigitalOcean. The code is already written - this is a deployment and configuration phase.

**Key Insight:** The Terraform modules and CI/CD workflow are complete. Work focuses on:
1. Account setup and secret generation
2. Terraform deployment execution
3. Resource validation
4. CI/CD enablement

## Prerequisites Checklist

Before starting, user must:
- [ ] Have DigitalOcean account access
- [ ] Know their DigitalOcean API token OR be able to create one
- [ ] Have access to GitHub repository secrets (epiphanyapps/chatbotAI)

## Tasks

### Task 1: Generate Required Secrets
**Goal:** Create all cryptographic secrets needed for deployment

**Steps:**
1. Generate JWT secret key:
   ```bash
   openssl rand -hex 32
   # Save output as JWT_SECRET_KEY
   ```

2. Generate encryption key:
   ```bash
   openssl rand -hex 32
   # Save output as ENCRYPTION_KEY
   ```

3. Get DigitalOcean API token:
   - Go to https://cloud.digitalocean.com/account/api/tokens
   - Click "Generate New Token"
   - Name: "chatbotai-terraform"
   - Scopes: Read + Write
   - Save output as DO_TOKEN

4. Get Stripe test key (for initial deployment):
   - Use existing test key OR
   - Go to https://dashboard.stripe.com/test/apikeys
   - Copy "Secret key" (starts with sk_test_)
   - Save as STRIPE_SECRET_KEY

**Outputs:**
- DO_TOKEN (required)
- JWT_SECRET_KEY (required)
- ENCRYPTION_KEY (required)
- STRIPE_SECRET_KEY (use test key)
- ALERT_EMAIL (your email)

**Verification:** All 5 secrets generated and saved securely

---

### Task 2: Initialize Terraform Backend
**Goal:** Configure Terraform for local state (initial deployment)

**Steps:**
1. Navigate to terraform directory:
   ```bash
   cd terraform
   ```

2. Create backend override for local state (temporary):
   ```bash
   cat > backend_override.tf << 'EOF'
   # Temporary local backend - will migrate to remote later
   terraform {
     backend "local" {
       path = "terraform.tfstate"
     }
   }
   EOF
   ```

3. Initialize Terraform:
   ```bash
   terraform init
   ```

4. Create dev workspace:
   ```bash
   terraform workspace new dev || terraform workspace select dev
   ```

**Outputs:**
- Terraform initialized
- Dev workspace created
- `.terraform/` directory populated

**Verification:** `terraform workspace show` returns "dev"

---

### Task 3: Deploy Dev Environment
**Goal:** Deploy infrastructure to DigitalOcean dev environment

**Steps:**
1. Set environment variables:
   ```bash
   export TF_VAR_do_token="<your_do_token>"
   export TF_VAR_stripe_secret_key="sk_test_..."
   export TF_VAR_jwt_secret_key="<generated_jwt_secret>"
   export TF_VAR_encryption_key="<generated_encryption_key>"
   export TF_VAR_alert_email="your@email.com"
   export TF_VAR_telegram_bot_token=""
   export TF_VAR_openai_api_key=""
   export TF_VAR_slack_webhook=""
   ```

2. Run Terraform plan:
   ```bash
   terraform plan -var-file="environments/dev/terraform.tfvars" -out=tfplan
   ```

3. Review plan output - expected resources:
   - 1 VPC
   - 1-2 Firewall rules
   - 1 PostgreSQL cluster
   - 1 Redis cluster
   - 1 App Platform app
   - 2-3 Uptime checks

4. Apply if plan looks correct:
   ```bash
   terraform apply tfplan
   ```

5. Wait for deployment (typically 10-15 minutes)

**Outputs:**
- All resources created in DigitalOcean
- terraform.tfstate updated

**Verification:** `terraform output` shows app_url and database URIs

---

### Task 4: Validate Deployed Resources
**Goal:** Confirm all infrastructure components are operational

**Steps:**
1. Get deployment outputs:
   ```bash
   terraform output
   # Note: app_url, postgres_private_uri, redis_private_uri
   ```

2. Check DigitalOcean Console:
   - Navigate to https://cloud.digitalocean.com
   - Verify VPC exists under Networking
   - Verify PostgreSQL cluster under Databases
   - Verify Redis cluster under Databases
   - Verify App exists under App Platform

3. Check App Platform deployment status:
   - App should show "Building" or "Deployed"
   - If failed, check build logs

4. Verify monitoring:
   - Navigate to Monitoring > Uptime in DO console
   - Check uptime alerts are created

**Outputs:**
- Screenshot or notes confirming each resource
- Any error messages if resources failed

**Verification:** All 5 success criteria from roadmap pass

---

### Task 5: Configure GitHub Secrets for CI/CD
**Goal:** Enable automated deployments via GitHub Actions

**Steps:**
1. Navigate to repository secrets:
   - Go to https://github.com/epiphanyapps/chatbotAI/settings/secrets/actions

2. Add each secret:
   | Secret Name | Value |
   |-------------|-------|
   | DO_TOKEN | DigitalOcean API token |
   | STRIPE_SECRET_KEY | Stripe test key |
   | STRIPE_WEBHOOK_SECRET | (leave empty for now) |
   | JWT_SECRET_KEY | Generated JWT secret |
   | TELEGRAM_BOT_TOKEN | (leave empty or existing bot) |
   | OPENAI_API_KEY | (leave empty - using Ollama) |
   | ENCRYPTION_KEY | Generated encryption key |
   | ALERT_EMAIL | Your alert email |
   | SLACK_WEBHOOK | (optional) |

3. Create GitHub Environments:
   - Go to repository Settings > Environments
   - Create "development" environment
   - Create "production" environment

**Outputs:**
- All secrets configured in GitHub
- Environments created

**Verification:** GitHub Actions > terraform-deploy workflow shows green on next push

---

### Task 6: Test CI/CD Pipeline
**Goal:** Verify automated deployment works

**Steps:**
1. Make a minor change to terraform (e.g., add comment):
   ```bash
   echo "# CI/CD test" >> terraform/main.tf
   ```

2. Commit and push to develop:
   ```bash
   git add terraform/main.tf
   git commit -m "test: verify CI/CD pipeline"
   git push origin develop
   ```

3. Monitor GitHub Actions:
   - Go to https://github.com/epiphanyapps/chatbotAI/actions
   - Watch "Terraform Infrastructure Deployment" workflow
   - Verify plan step succeeds
   - Verify apply step succeeds

4. Revert test change:
   ```bash
   git revert HEAD
   git push origin develop
   ```

**Outputs:**
- Successful GitHub Actions run
- Deployment verified

**Verification:** GitHub Actions shows successful deployment

---

## Rollback Plan

If deployment fails:

1. **Terraform apply fails mid-way:**
   ```bash
   terraform destroy -var-file="environments/dev/terraform.tfvars"
   # Fix configuration
   # Re-run terraform apply
   ```

2. **Resources created but broken:**
   - Check DigitalOcean console for specific errors
   - Database connection issues: Check VPC firewall rules
   - App Platform failures: Check build logs

3. **CI/CD fails:**
   - Check GitHub Actions logs
   - Verify secrets are set correctly
   - Try manual deployment to isolate issue

## Success Criteria Verification

| Criteria | How to Verify | Command/Action |
|----------|---------------|----------------|
| Terraform applies successfully | Exit code 0 | `terraform apply` completes |
| PostgreSQL accepts connections | Connection string works | `terraform output postgres_private_uri` |
| Redis accepts connections | Connection string works | `terraform output redis_private_uri` |
| SSL certificates auto-renew | App Platform config | Check DO console |
| Uptime monitoring triggers | Alerts created | Check DO Monitoring |

## Estimated Cost After Deployment

- **Monthly:** ~$150/month for dev environment
- **Breakdown:**
  - PostgreSQL: $60
  - Redis: $15
  - App Platform: $50
  - Storage/Monitoring: $25

## Next Phase Dependencies

Phase 2 (Authentication & Legal) requires:
- ✅ PostgreSQL running (user accounts table)
- ✅ Redis running (session storage)
- ✅ App Platform deployed (backend API)
- Domain purchased (for production SSL)

---
*Plan ready for execution.*
