# Requirements: IntimateAI

**Defined:** 2026-02-21
**Core Value:** Users can have explicit, uncensored conversations with Sophia that feel personal and engaging enough to pay monthly.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Infrastructure

- [ ] **INFRA-01**: Deploy Terraform infrastructure to DigitalOcean (Issue #12)
- [ ] **INFRA-02**: PostgreSQL managed database for user data and conversations
- [ ] **INFRA-03**: Redis managed database for sessions and caching
- [ ] **INFRA-04**: SSL/HTTPS via Let's Encrypt certificates
- [ ] **INFRA-05**: Uptime monitoring and alerting configured

### Authentication

- [x] **AUTH-01**: User can sign up via magic link email (passwordless)
- [x] **AUTH-02**: User must verify email before accessing trial
- [x] **AUTH-03**: User must confirm 18+ age before accessing service
- [x] **AUTH-04**: System blocks disposable email domains
- [x] **AUTH-05**: System fingerprints devices to prevent trial abuse
- [x] **AUTH-06**: JWT session management with secure tokens

### Web Chat

- [ ] **CHAT-01**: User can chat with Sophia via real-time WebSocket in browser
- [ ] **CHAT-02**: User sees typing indicator when Sophia is "responding"
- [ ] **CHAT-03**: Chat interface is mobile responsive
- [ ] **CHAT-04**: Conversation history persists and loads on reconnect
- [ ] **CHAT-05**: Same personality system (TF-IDF + Ollama) serves web chat

### Payments

- [ ] **PAY-01**: User can subscribe at $29.99/month via Stripe
- [ ] **PAY-02**: New users get 2-hour free trial before payment required
- [ ] **PAY-03**: System handles Stripe webhooks securely (signature verification)
- [ ] **PAY-04**: Chat access gated by subscription status
- [ ] **PAY-05**: Trial expires automatically after 2 hours

### Legal & Compliance

- [ ] **LEGAL-01**: Terms of Service page (adult content specific)
- [ ] **LEGAL-02**: Privacy Policy page (GDPR/CCPA compliant)
- [x] **LEGAL-03**: Age verification gate (18+ confirmation with audit trail)

### Landing Page

- [ ] **LAND-01**: Landing page at IntimateAI.chat with value proposition
- [ ] **LAND-02**: Clear call-to-action to start free trial
- [ ] **LAND-03**: Age verification before accessing chat

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Telegram Integration

- **TELE-01**: User can chat with Sophia via Telegram (premium feature)
- **TELE-02**: User can link web account to Telegram
- **TELE-03**: Same personality serves both channels

### Sophia Improvements

- **SOPH-01**: More response variety (reduce repetition)
- **SOPH-02**: Better conversation context tracking

### Additional Personalities

- **PERS-01**: Emma personality (loving cuckoldress)
- **PERS-02**: Madison personality (bratty hotwife)
- **PERS-03**: Isabella personality (Latina hotwife)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| OpenAI/Claude API | Guardrails block adult content; using local Ollama |
| OAuth login (Google, etc.) | Magic link is simpler and more private |
| Mobile apps | Web-first with responsive design covers mobile |
| Real-time user-to-user chat | This is AI companion, not social platform |
| Image generation | High complexity, unclear demand, legal risk |
| Voice messages | Defer until text chat validated |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | Phase 1 | Pending |
| INFRA-02 | Phase 1 | Pending |
| INFRA-03 | Phase 1 | Pending |
| INFRA-04 | Phase 1 | Pending |
| INFRA-05 | Phase 1 | Pending |
| AUTH-01 | Phase 2 | Complete |
| AUTH-02 | Phase 2 | Complete |
| AUTH-03 | Phase 2 | Complete |
| AUTH-04 | Phase 2 | Complete |
| AUTH-05 | Phase 2 | Complete |
| AUTH-06 | Phase 2 | Complete |
| CHAT-01 | Phase 3 | Pending |
| CHAT-02 | Phase 3 | Pending |
| CHAT-03 | Phase 3 | Pending |
| CHAT-04 | Phase 3 | Pending |
| CHAT-05 | Phase 3 | Pending |
| PAY-01 | Phase 4 | Pending |
| PAY-02 | Phase 4 | Pending |
| PAY-03 | Phase 4 | Pending |
| PAY-04 | Phase 4 | Pending |
| PAY-05 | Phase 4 | Pending |
| LEGAL-01 | Phase 2 | Pending |
| LEGAL-02 | Phase 2 | Pending |
| LEGAL-03 | Phase 2 | Complete |
| LAND-01 | Phase 5 | Pending |
| LAND-02 | Phase 5 | Pending |
| LAND-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-21*
*Last updated: 2026-02-21 after initial definition*
