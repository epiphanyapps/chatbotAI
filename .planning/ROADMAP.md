# Roadmap: IntimateAI

## Overview

Transform existing Telegram bot and Terraform infrastructure into a production-ready web-first adult AI companion SaaS. Starting with infrastructure deployment, then building out authentication and legal foundation, core web chat experience, payment integration for $29.99/month subscriptions, and finally landing page for public launch. Every phase delivers observable user capabilities.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Infrastructure Deployment** - Deploy Terraform to DigitalOcean with databases and monitoring (2026-02-21)
- [ ] **Phase 2: Authentication & Legal Foundation** - Passwordless auth and adult content compliance
- [ ] **Phase 3: Web Chat Experience** - Real-time browser chat with Sophia personality
- [ ] **Phase 4: Payments & Subscriptions** - Stripe integration with 2-hour free trial
- [ ] **Phase 5: Landing Page & Launch** - Public-facing site with age verification

## Phase Details

### Phase 1: Infrastructure Deployment
**Goal**: Production infrastructure running on DigitalOcean with monitoring
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. Terraform applies successfully to DigitalOcean account
  2. PostgreSQL managed database accepts connections
  3. Redis managed database accepts connections
  4. SSL certificates auto-renew via Let's Encrypt
  5. Uptime monitoring alerts trigger on service failures
**Plans**: .planning/phases/01-infrastructure/01-01-PLAN.md

Plans:
- [x] 01-01: Infrastructure Deployment (2026-02-21)
  - PostgreSQL, Valkey (Redis), App Platform deployed
  - GitHub secrets and environments configured
  - Live: https://chatbotai-dev-f9xc3.ondigitalocean.app

### Phase 2: Authentication & Legal Foundation
**Goal**: Users can create accounts and access service with legal compliance
**Depends on**: Phase 1
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, AUTH-06, LEGAL-01, LEGAL-02, LEGAL-03
**Success Criteria** (what must be TRUE):
  1. User receives magic link email and can log in without password
  2. User must verify email before accessing trial
  3. User must confirm 18+ age before accessing service (with audit trail)
  4. System blocks disposable email domains (guerrillamail, tempmail, etc.)
  5. User sessions persist across browser restarts via JWT tokens
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 3: Web Chat Experience
**Goal**: Users can chat with Sophia in real-time via browser
**Depends on**: Phase 2
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05
**Success Criteria** (what must be TRUE):
  1. User can send message and receive Sophia response in under 3 seconds
  2. User sees typing indicator when Sophia is generating response
  3. Chat interface works on mobile browsers (iOS Safari, Chrome Android)
  4. User reconnects and sees full conversation history
  5. Sophia personality feels consistent with existing Telegram bot
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 4: Payments & Subscriptions
**Goal**: Users can subscribe at $29.99/month with 2-hour trial
**Depends on**: Phase 3
**Requirements**: PAY-01, PAY-02, PAY-03, PAY-04, PAY-05
**Success Criteria** (what must be TRUE):
  1. User can start 2-hour trial without entering payment information
  2. User can subscribe via Stripe checkout after trial expires
  3. Chat access blocks when trial expires and subscription is inactive
  4. System receives and processes Stripe webhooks securely
  5. Trial timer displays countdown and expires automatically after 2 hours
**Plans**: TBD

Plans:
- [ ] TBD

### Phase 5: Landing Page & Launch
**Goal**: Public can discover and access IntimateAI.chat
**Depends on**: Phase 4
**Requirements**: LAND-01, LAND-02, LAND-03
**Success Criteria** (what must be TRUE):
  1. Landing page loads at IntimateAI.chat with clear value proposition
  2. Call-to-action button starts trial signup flow
  3. Age verification gate blocks access for users who decline 18+ confirmation
**Plans**: TBD

Plans:
- [ ] TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Infrastructure Deployment | 1/1 | ✓ Complete | 2026-02-21 |
| 2. Authentication & Legal Foundation | 0/? | Not started | - |
| 3. Web Chat Experience | 0/? | Not started | - |
| 4. Payments & Subscriptions | 0/? | Not started | - |
| 5. Landing Page & Launch | 0/? | Not started | - |
