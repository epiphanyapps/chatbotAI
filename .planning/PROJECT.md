# IntimateAI - Adult AI Companion SaaS

## What This Is

A web-based adult AI companion service targeting the hotwife/cuckold market. Users chat with distinct AI personalities (starting with Sophia) through a browser interface, with Telegram available as a premium channel. Subscription-based model at $29.99/month with a 2-hour free trial.

## Core Value

Users can have explicit, uncensored conversations with an AI that feels like a real personality — not a generic chatbot. The experience must feel personal and engaging enough that users pay monthly.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Sophia personality implementation — existing (TF-IDF + personality flair)
- ✓ Training data (175 conversations) — existing
- ✓ Terraform infrastructure for DigitalOcean — existing
- ✓ Docker deployment setup — existing

### Active

<!-- Current scope. Building toward these. -->

**Authentication & Users:**
- [ ] Magic link email authentication (no passwords)
- [ ] User accounts with email as primary identity
- [ ] Session management with JWT tokens

**Web Chat Interface:**
- [ ] Real-time browser chat (WebSocket)
- [ ] Mobile-responsive design
- [ ] Typing indicators and natural message timing
- [ ] Conversation history persistence

**Subscription & Payments:**
- [ ] Stripe integration for $29.99/month subscription
- [ ] 2-hour free trial with automatic expiration
- [ ] Subscription status checking before chat access
- [ ] Webhook handling for payment events

**Sophia Personality Improvements:**
- [ ] More response variety (reduce repetition)
- [ ] Conversation context tracking (remember flow)
- [ ] Same TF-IDF system (no API costs)

**Telegram Channel (Premium):**
- [ ] Telegram bot integration
- [ ] Link Telegram to web account
- [ ] Same personality serving both channels

**Landing Page & Legal:**
- [ ] IntimateAI.chat landing page
- [ ] Age verification (18+)
- [ ] Terms of Service (adult content)
- [ ] Privacy Policy (GDPR/CCPA)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Additional personalities (Emma, Madison, Isabella) — v2 after Sophia is solid
- OAuth login (Google, etc.) — magic link is simpler
- OpenAI/Claude API — guardrails block adult content; using local Ollama instead
- Mobile apps — web-first, responsive design covers mobile
- Real-time chat between users — this is AI companion, not social

## Context

**Existing Codebase:**
- `multi_personality_bot.py` — working bot with TF-IDF matching
- `personalities/` — personality system with Sophia implemented
- `terraform/` — DigitalOcean infrastructure ready
- `docker-compose.yml` — container orchestration configured

**Technical Approach:**
- Python backend (FastAPI)
- React frontend for web chat
- PostgreSQL for user data and conversations
- Redis for sessions and rate limiting
- WebSocket for real-time messaging
- Local Ollama for AI generation (no guardrails, no API costs)
- TF-IDF for response matching from training data

**Market Context:**
- Hotwife/cuckold niche is underserved in AI companions
- Adult content requires specific merchant approval (Stripe ~30 days)
- Users value privacy — Telegram option addresses this

**Known Sophia Issues:**
- Repetitive responses — needs more training examples or better selection
- Context loss — doesn't track conversation state well

## Constraints

- **Budget**: Zero external API costs — local Ollama + TF-IDF matching
- **Hosting**: DigitalOcean ($12/mo droplet tier)
- **Domain**: IntimateAI.chat (not yet purchased)
- **Payments**: Stripe adult merchant approval required (~30 days)
- **Legal**: 18+ age verification, adult-specific ToS required

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web-first architecture | 15x larger market than Telegram-only | — Pending |
| Magic link auth | No passwords = simpler UX | — Pending |
| Local Ollama + TF-IDF | No guardrails + zero API costs | — Pending |
| 2-hour trial | Creates urgency, matches adult content patterns | — Pending |
| DigitalOcean hosting | Terraform already built, $12/mo starting tier | — Pending |

---
*Last updated: 2026-02-21 after initialization*
