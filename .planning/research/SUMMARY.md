# Research Summary: IntimateAI Web Chat Extension

**Domain:** Adult AI Companion SaaS (Web-first architecture milestone)
**Researched:** 2026-02-21
**Overall confidence:** MEDIUM

## Research Limitations

WebSearch and Bash tools were unavailable during this research session. Analysis is based on:
1. Official FastAPI documentation (WebSocket implementation - HIGH confidence)
2. Existing codebase context (.planning/PROJECT.md, .planning/codebase/STACK.md)
3. Training data knowledge (January 2025 cutoff)

**Critical gaps:** Unable to verify current frontend library versions, email service pricing, or competitor feature sets. Recommend validating technology versions before implementation.

## Executive Summary

The standard 2026 stack for real-time AI companion web apps centers on **FastAPI + native WebSocket** for backend real-time communication, **React 18 + Vite** for frontend development, and **native browser WebSocket API** (not Socket.io) for client connections. The adult content vertical adds specific requirements: Stripe high-risk merchant approval, robust age verification with audit trails, content moderation despite using local AI, and GDPR-compliant encryption for sensitive conversation data.

The existing Telegram bot codebase provides a solid foundation. The personality system (TF-IDF + Sophia) can be preserved as-is. The critical architectural shift is extracting channel-agnostic business logic into a unified message router, allowing the same personality engine to serve both web and Telegram channels. This requires refactoring but not rewriting the existing bot.

Key findings favor simplicity: native WebSocket over Socket.io (lighter, standard protocol), magic link auth over OAuth (privacy-conscious, no third-party tracking), and Resend over complex email infrastructure (developer-friendly, adequate free tier). The zero-API-cost constraint (local Ollama) is technically viable but requires content filtering layers to prevent prompt injection attacks that could generate illegal content.

The most critical non-technical risk is payment processor compliance. Stripe requires explicit adult content merchant approval with 7-30 day lead time. The 2-hour trial mechanism requires careful implementation to prevent abuse while maintaining conversion rates. Age verification is both a legal requirement and a payment processor prerequisite — shortcuts here risk account termination and legal liability.

## Key Findings

**Stack:** FastAPI (WebSocket native) + React 18 (Vite build) + PostgreSQL (ACID for subscriptions) + Redis (sessions + pub/sub) + native WebSocket API (no Socket.io bloat)

**Architecture:** Channel adapter pattern for multi-platform support (web + Telegram), unified message router for channel-agnostic business logic, Redis pub/sub for horizontal WebSocket scaling (defer until needed)

**Critical pitfall:** Payment processor due diligence — Stripe adult content merchant approval must happen 30+ days before launch. Account termination mid-launch kills revenue with no quick recovery.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 0: Pre-Launch Compliance (Before any code)
**Duration:** 2-4 weeks (parallel to Phase 1 development)
**Rationale:** Legal and payment blockers have long lead times. Starting coding without addressing these risks launch delays.

- **Addresses:** Payment processor compliance, age verification legal review, 18 USC 2257 assessment
- **Avoids:** Stripe account termination (PITFALLS.md #1), legal liability for inadequate age verification (#2), 2257 non-compliance (#3)
- **Deliverables:**
  - Stripe high-risk merchant account applied (30-day approval timeline)
  - Attorney consultation on adult content compliance (age verification, 2257, GDPR)
  - Privacy Policy and Terms of Service drafted (adult-specific clauses)
  - Domain purchased (IntimateAI.chat) with adult-content-friendly registrar
  - Age verification strategy documented (third-party service vs self-implemented)

### Phase 1: Authentication & Foundation (Week 1-2)
**Rationale:** Everything depends on user identity and session management. WebSocket connections require JWT validation. Subscriptions require user accounts.

- **Addresses:** Magic link authentication, JWT session management, age verification implementation, database models
- **Avoids:** Trial abuse (#9), session hijacking (#10), inadequate age verification (#2)
- **Deliverables:**
  - PostgreSQL schema (users, messages, sessions tables)
  - Redis session store with JWT tokens
  - Magic link email flow (Resend integration)
  - Email verification before trial access
  - Age verification gate (18+ with audit trail)
  - Disposable email domain blocking
  - Device fingerprinting for trial abuse prevention

**Dependencies:** Stripe merchant approval (from Phase 0) not required yet. Email service (Resend) can be set up quickly.

### Phase 2: Core WebSocket Chat (Week 2-3)
**Rationale:** Core product experience. Once auth works, WebSocket chat is the MVP. Personality engine already exists in Telegram bot.

- **Addresses:** Real-time chat interface, WebSocket connection management, personality integration, conversation persistence
- **Avoids:** Prompt injection attacks (#4), GDPR non-compliance (#5), synchronous blocking in handlers (ARCHITECTURE.md anti-pattern #3)
- **Deliverables:**
  - FastAPI WebSocket endpoint with JWT authentication
  - ConnectionManager (in-memory, single instance)
  - Extract personality engine from multi_personality_bot.py
  - Implement channel adapter pattern (base + web adapter)
  - Unified message router (channel-agnostic)
  - Content moderation filters (keyword blocklist for illegal content)
  - Message persistence to PostgreSQL (encrypted at rest)
  - Conversation history loading for context

**Dependencies:** Phase 1 auth system. Stripe not required yet (trial doesn't need payment).

### Phase 3: Frontend Chat UI (Week 3-4)
**Rationale:** Backend WebSocket works, now build the user-facing interface. Mobile-responsive critical (70%+ mobile traffic for adult content).

- **Addresses:** React chat interface, WebSocket client, typing indicators, mobile responsiveness
- **Avoids:** UX pitfalls (slow responses, no typing indicator, poor mobile experience)
- **Deliverables:**
  - Vite + React + TypeScript project scaffold
  - TailwindCSS styling (mobile-first)
  - WebSocket connection hook (useWebSocket)
  - Chat message display component
  - Message input with send/typing detection
  - Typing indicator animation
  - Connection status handling (reconnection logic)
  - Message history scroll loading
  - Trial timer countdown display

**Dependencies:** Phase 2 WebSocket API. No Stripe dependency yet.

### Phase 4: Payments & Subscription (Week 4-5)
**Rationale:** Trial works, now monetize. Stripe merchant approval should be complete by now (started in Phase 0). Webhook security critical before processing real money.

- **Addresses:** Stripe subscription integration, trial-to-paid conversion, webhook handling, chargeback prevention
- **Avoids:** Webhook security bypass (#8), chargeback issues (#6), subscription status race conditions
- **Deliverables:**
  - Stripe subscription creation (checkout flow)
  - Stripe webhook endpoint (signature verification!)
  - Webhook event handlers (subscription created, updated, deleted, payment failed)
  - Trial expiration enforcement (2-hour countdown)
  - Subscription status caching (Redis)
  - Email receipts (immediate after charge)
  - Pre-charge reminder emails (3 days, 1 day before)
  - Clear billing descriptor configuration
  - Cancellation flow (easy, no confirmation)
  - Customer support contact display

**Dependencies:** Stripe merchant approval (from Phase 0). Auth system (Phase 1). WebSocket chat (Phase 2). Frontend (Phase 3).

### Phase 5: Telegram Integration (Week 5-6)
**Rationale:** Premium differentiator. Existing bot code can be wrapped in channel adapter. Unified router makes this straightforward.

- **Addresses:** Telegram bot integration, account linking, multi-channel personality consistency
- **Avoids:** Telegram rate limiting (#7), channel-specific logic in core (ARCHITECTURE.md anti-pattern #1)
- **Deliverables:**
  - Telegram adapter implementing channel interface
  - Account linking flow (Telegram user → web account)
  - Telegram webhook handler
  - Rate limiting queue (20 msg/min global, 1/sec per chat)
  - 429 error handling with exponential backoff
  - Subscription status check before Telegram access
  - Message batching for long responses
  - Health monitoring (getMe API)

**Dependencies:** Unified router (Phase 2). Subscription system (Phase 4). Telegram bot already exists, just needs adapter wrapper.

### Phase 6: Polish & Launch Prep (Week 6-7)
**Rationale:** Feature-complete, now ensure production readiness. Legal compliance, monitoring, edge cases.

- **Addresses:** Data export/deletion (GDPR), monitoring, error handling, edge case testing
- **Avoids:** GDPR violations (#5), production incidents without observability
- **Deliverables:**
  - User data export feature (GDPR Article 15)
  - Account deletion feature (GDPR Article 17)
  - Privacy policy implementation (cookie banner, consent)
  - Error logging (Sentry or similar)
  - Uptime monitoring (UptimeRobot or similar)
  - Load testing (simulate 100 concurrent WebSocket connections)
  - Security audit (age verification bypass attempts, content filter evasion)
  - Backup strategy (PostgreSQL automated backups)
  - Runbook for common incidents (Stripe webhook failure, Telegram bot ban, database connection exhaustion)

**Dependencies:** All previous phases. Legal documents from Phase 0.

## Phase Ordering Rationale

### Why Auth First?
Every feature (WebSocket, subscriptions, Telegram linking) requires user identity. Building chat without auth means throwing away work. Session management is the foundation.

### Why WebSocket Before Frontend?
Backend-first validates the architecture. WebSocket API can be tested with Postman or simple HTML before React complexity. Easier debugging.

### Why Payments Before Telegram?
Telegram is premium feature. No point building premium channel if monetization doesn't work. Stripe integration is riskier (compliance, webhooks) than Telegram wrapping.

### Why Not Start with Telegram Refactor?
Existing Telegram bot works. Wrapping it in adapter is low-risk. Refactoring without web channel to validate the abstraction is premature. Build web first, then retrofit Telegram.

## Research Flags for Phases

**Phase 0 (Pre-Launch Legal):** Likely needs deeper research
- 18 USC 2257 applicability to AI-generated text content is legally uncertain
- Attorney consultation required (not just internet research)
- Stripe adult content policy may have changed since training data (verify current requirements)

**Phase 1 (Authentication):** Standard patterns, unlikely to need research
- Magic link implementation is well-documented
- JWT best practices are established
- Email verification is standard

**Phase 2 (WebSocket Chat):** Likely needs deeper research
- Content moderation strategy for local AI (no external API guardrails)
- Prompt injection prevention techniques specific to adult content
- Conversation encryption implementation details (which fields, key management)

**Phase 3 (Frontend):** Likely needs deeper research
- React WebSocket reconnection strategies (exponential backoff parameters)
- Mobile chat UI performance (message virtualization thresholds)
- Frontend state management choice (Context API sufficient vs Zustand/Redux)

**Phase 4 (Payments):** Standard patterns, unlikely to need research
- Stripe subscription webhooks are well-documented
- Chargeback prevention is established domain knowledge
- Email receipt timing is standard practice

**Phase 5 (Telegram):** Standard patterns, unlikely to need research
- Telegram Bot API is well-documented
- Rate limiting patterns are established
- Account linking flows are standard

**Phase 6 (Launch Prep):** Likely needs validation research
- GDPR data export format requirements
- Production monitoring tool selection (self-hosted vs SaaS)
- Load testing parameters for adult content SaaS (unusual usage patterns)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | FastAPI verified HIGH (official docs). Frontend versions LOW (training data, not verified). Email services LOW (pricing may be stale). Overall MEDIUM. |
| Features | LOW | Unable to verify competitor features (Character.AI, Replika, adult-specific platforms). Feature priorities based on training data + project context. Trial length (2 hours) not validated against market. |
| Architecture | MEDIUM-HIGH | Channel adapter pattern is standard. FastAPI WebSocket implementation verified with official docs (HIGH). Redis pub/sub pattern is established. Frontend architecture not verified (MEDIUM). |
| Pitfalls | MEDIUM | Legal compliance (GDPR, 2257, age verification) based on training data + established law, but adult content enforcement priorities may have shifted. Payment processor requirements may have changed. Telegram rate limits may have changed. Content moderation techniques not verified with current sources. |

### Confidence Breakdown

**HIGH confidence (verified with authoritative sources):**
- FastAPI WebSocket implementation (official docs)
- PostgreSQL, Redis usage patterns (existing codebase)
- Channel adapter architectural pattern (standard SaaS pattern)

**MEDIUM confidence (training data + ecosystem standards, not verified):**
- React 18, Vite 5, TypeScript 5 as current versions
- SQLAlchemy 2.0, Pydantic 2 versions
- Stripe SDK version estimates
- GDPR compliance requirements (law is stable but enforcement priorities may shift)
- Chargeback prevention strategies

**LOW confidence (training data only, needs verification):**
- Email service pricing (Resend, SES, Postmark)
- Competitor feature analysis (market may have shifted significantly)
- Trial length best practices (2 hours may be too short/long)
- 18 USC 2257 applicability to AI-generated content (legal gray area)
- Frontend library versions (React, Vite, TailwindCSS may have had major releases)

## Gaps to Address

### Legal & Compliance Gaps
- **18 USC 2257 AI applicability:** Training data indicates this is a gray area. Attorney consultation required to determine if text-only AI responses trigger record-keeping requirements. If adding AI-generated images later, compliance is almost certainly required.
- **Age verification adequacy:** Simple checkbox + date of birth may not satisfy payment processors or regulators. Research third-party age verification APIs (Yoti, Jumio, AgeChecker.Net) for current pricing and integration complexity.
- **International compliance:** GDPR covered, but what about Canada (PIPEDA), Australia (Privacy Act), California (CCPA/CPRA)? Scope: US-only launch, or broader?

### Technology Verification Gaps
- **Frontend library versions:** All React ecosystem versions (React, Vite, TailwindCSS, TypeScript) based on training data. Verify current stable versions before `npm install`. Check for breaking changes in major versions.
- **Email service current pricing:** Resend free tier (100 emails/day) may have changed. Verify before committing. Check Postmark and SES current pricing for backup options.
- **Stripe adult content requirements:** Merchant approval process may have changed since training data. Verify current application requirements, approval timeline, and restricted content policies.

### Market Validation Gaps
- **Competitor features:** Unable to verify what Replika, Character.AI, Candy.ai, Dreamgf.ai currently offer. May have added features that are now table stakes (voice messages, image generation, advanced memory). Validate before finalizing roadmap.
- **Trial length standards:** 2-hour trial chosen based on training data patterns. Current market may expect longer (24 hours) or shorter (10 messages) trials. A/B testing recommended.
- **Pricing:** $29.99/month based on project context. Validate against current competitor pricing. Adult AI companions may have shifted to $15-20/month or $40-50/month ranges.

### Architecture Validation Gaps
- **Content moderation for local AI:** Training data suggests keyword blocklists + external moderation API (OpenAI Moderation, Perspective API). Validate current best practices for preventing prompt injection attacks in adult content AI.
- **WebSocket scaling thresholds:** "10k-65k connections per instance" based on general knowledge. Actual limits depend on OS (ulimit), hardware (RAM), and message frequency. Load testing required.
- **Conversation encryption implementation:** AES-256 encryption recommended, but key management strategy not researched. Where are encryption keys stored? Per-user keys or single master key? Key rotation strategy?

### Product Validation Gaps
- **Sophia personality quality:** PROJECT.md notes repetition and context loss issues. Unknown if TF-IDF + Ollama can match user expectations formed by ChatGPT/Claude-quality AI. May need OpenAI API despite guardrails (fine-tuning to bypass adult content restrictions).
- **2-hour trial conversion rate:** Expected 15-20% conversion based on training data. Adult content may have different conversion patterns. Metrics-driven optimization required.
- **Telegram as premium feature value:** Unknown if users actually value Telegram integration enough to pay. May be solving a non-problem. User interviews recommended.

## Recommendations for Roadmap Creation

### Must Validate Before Finalizing Roadmap
1. **Verify current frontend library versions** — Run `npm info react version`, `npm info vite version` before committing to stack
2. **Check Stripe adult content policy** — Visit stripe.com/restricted-businesses and confirm current requirements
3. **Attorney consultation on 18 USC 2257** — Schedule before Phase 0 starts, blocks launch if required

### Must Research During Implementation
1. **Phase 2:** Content moderation strategy research — How to prevent prompt injection attacks with local AI
2. **Phase 3:** Frontend WebSocket patterns research — Current best practices for reconnection, state management
3. **Phase 4:** Stripe webhook testing research — Validate signature verification, idempotency, event handling

### Must Test Before Launch
1. **Phase 5:** Telegram rate limit testing — Verify 429 handling works, measure actual throughput limits
2. **Phase 6:** Load testing — Simulate 100 concurrent WebSocket connections, measure breaking point
3. **Phase 6:** Security testing — Age verification bypass attempts, content filter evasion, trial abuse

### Recommended Validation Activities
- **Competitor analysis:** Sign up for Replika, Character.AI, Candy.ai trials. Document feature set, pricing, trial mechanics, personality quality.
- **User interviews:** Talk to 5-10 hotwife/cuckold community members. Validate problem, feature priorities, pricing tolerance.
- **A/B testing plan:** 2-hour vs 24-hour trial, $29.99 vs $19.99 pricing, magic link vs OAuth (after launch, with analytics).

## Success Criteria for Research Phase

- [x] Stack recommendations provided with specific versions
- [x] Architecture patterns documented with code examples
- [x] Feature landscape mapped (table stakes, differentiators, anti-features)
- [x] Critical pitfalls catalogued with prevention strategies
- [x] Phase structure suggested with rationale
- [x] Research gaps identified and flagged
- [x] Confidence levels assigned to all findings
- [x] Verification sources documented

**Research complete.** Roadmap creation can proceed with awareness of confidence levels and validation gaps.

---
*Research Summary for: IntimateAI Web Chat Extension*
*Researched: 2026-02-21*
*Confidence: MEDIUM overall (HIGH for backend architecture, LOW for market validation)*
