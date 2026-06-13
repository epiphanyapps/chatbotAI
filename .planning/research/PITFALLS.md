# Pitfalls Research

**Domain:** Adult AI Companion SaaS
**Researched:** 2026-02-21
**Confidence:** MEDIUM (Training data + project context; unable to verify with current sources)

## Critical Pitfalls

### Pitfall 1: Inadequate Payment Processor Due Diligence

**What goes wrong:**
Payment processor account gets terminated without warning, cutting off all revenue. Merchant account is frozen or banned mid-launch due to "high-risk" category violations or inadequate disclosure of adult content nature.

**Why it happens:**
- Adult content is not explicitly disclosed during merchant application
- Payment processor's "acceptable use policy" interpretation changes
- Chargeback rates exceed processor tolerance (often >1% for adult content)
- Missing required documentation (business license, age verification systems)
- Using standard merchant accounts instead of high-risk merchant accounts

**How to avoid:**
1. **Explicitly disclose adult content** during Stripe application (use "Adult Digital Content" category)
2. Apply for high-risk merchant account upfront (30+ day approval process)
3. Implement robust age verification before ANY content access
4. Document chargeback prevention measures (clear billing descriptors, refund policy)
5. Have backup payment processor ready (CCBill, Epoch, SegPay specialize in adult content)
6. Review Stripe's Restricted Businesses policy monthly for changes
7. Maintain detailed records of age verification and content moderation

**Warning signs:**
- Application approval takes less than 7 days (likely didn't review adult content properly)
- Account representative doesn't ask about age verification systems
- "Processing hold" emails or delayed payouts
- Sudden increase in chargeback notifications
- Generic merchant account instead of explicit adult content approval

**Phase to address:**
Phase 0 (Pre-launch) — Before integrating Stripe, before accepting any payments

---

### Pitfall 2: Non-Compliant Age Verification

**What goes wrong:**
Legal liability for providing adult content to minors. Regulatory fines (up to $100k+ per violation under some jurisdictions). Payment processor termination. Domain registrar suspension. Hosting provider account closure.

**Why it happens:**
- Simple "I am 18+" checkbox treated as sufficient verification
- No documentation or audit trail of verification
- Age verification happens after content exposure
- IP-based geolocation used without identity verification
- Verification system bypassed by clearing cookies

**How to avoid:**
1. **Gate ALL content** behind age verification — no previews, no trial content before verification
2. Implement third-party age verification service (AgeChecker.Net, Yoti, Jumio)
3. Require government ID verification for subscription activation
4. Store verification timestamp and method in database
5. Re-verify if user clears cookies or switches devices
6. Document verification process in Terms of Service
7. Display age verification badge/certification on landing page
8. Implement geo-blocking for jurisdictions with stricter requirements

**Warning signs:**
- Age verification can be bypassed by browser back button
- No database record of who was verified and when
- Verification happens after conversation starts
- Cookie deletion allows re-entry without verification
- No legal review of age verification adequacy

**Phase to address:**
Phase 1 (Authentication & Landing) — Must be production-ready before any public access

---

### Pitfall 3: 18 USC 2257 Record-Keeping Non-Compliance

**What goes wrong:**
Federal criminal liability for failure to maintain required records for "visual depictions of sexually explicit conduct." Even AI-generated content that appears realistic may trigger this requirement. Fines and potential imprisonment for non-compliance.

**Why it happens:**
- Assumption that AI-generated content is exempt (legal uncertainty)
- No custodian of records designated
- Missing records of content creation and participant age
- Records not maintained at physical US location
- Failure to display 2257 exemption statement or custodian location

**How to avoid:**
1. **Consult adult entertainment attorney** immediately — this is complex federal law
2. If using any images/video (even AI-generated realistic depictions):
   - Designate custodian of records
   - Maintain physical records at US address
   - Display 2257 compliance statement on every page with visual content
3. **Text-only AI responses may be safer** — avoid image generation entirely in MVP
4. Document legal opinion on whether AI-generated content triggers 2257
5. If uncertain, assume compliance is required and implement full record-keeping
6. Update Terms of Service with 2257 exemption or compliance statement

**Warning signs:**
- No attorney consultation on 2257 applicability
- Using realistic AI-generated images without record-keeping
- No custodian of records designated
- Missing 2257 statement on pages with visual content
- Hosting provider questions 2257 compliance

**Phase to address:**
Phase 0 (Pre-launch Legal Review) — Before adding any visual content features

---

### Pitfall 4: Prompt Injection Attacks Creating Illegal Content

**What goes wrong:**
Users manipulate AI prompts to generate content involving minors, non-consent scenarios, or other illegal content. Site becomes liable for hosting illegal material. Law enforcement investigation. Domain seizure. Criminal charges for operators.

**Why it happens:**
- AI model has no hard content filters (local Ollama without guardrails)
- Training data includes problematic content
- Prompt injection bypasses weak keyword filters
- No content moderation or review of generated responses
- Logs don't capture user prompts that triggered problematic content

**How to avoid:**
1. **Implement hard keyword blocklists** for illegal content categories (minors, animals, non-consent)
2. Filter both user input AND AI-generated output before display
3. Monitor and log all conversations — flag suspicious patterns
4. Implement report/block functionality for users
5. Use content moderation API (OpenAI Moderation API, Perspective API) even with local AI
6. Establish clear content policy and enforce with automated + human review
7. Training data audit — remove any problematic examples
8. Rate limit conversation depth to prevent iterative prompt injection
9. Implement "safety layer" AI review before response display

**Warning signs:**
- No content filtering on AI responses
- Training data not reviewed for illegal content
- No abuse reporting mechanism
- Conversation logs not monitored
- Users discuss "jailbreaking" the AI in community spaces
- No automated content moderation

**Phase to address:**
Phase 1 (Core Chat) — Before enabling real-time AI conversations

---

### Pitfall 5: GDPR/CCPA Non-Compliance for Sensitive Data

**What goes wrong:**
Regulatory fines (up to €20M or 4% of revenue under GDPR). User lawsuits for privacy violations. Data breach notification failures. Hosting provider suspension. Adult content chat logs are "sensitive personal data" requiring heightened protection.

**Why it happens:**
- Adult chat logs stored without encryption
- No data retention policy (logs kept indefinitely)
- Missing user data export/deletion features
- No privacy policy or inadequate disclosures
- Data shared with third parties (analytics, payment processors) without consent
- Conversation history accessible without authentication

**How to avoid:**
1. **Encrypt conversation logs at rest and in transit** (AES-256, TLS 1.3)
2. Implement data retention policy — auto-delete logs after 90 days unless user opts in
3. Provide user data export (GDPR Article 15) and deletion (GDPR Article 17) features
4. Obtain explicit consent before collecting any data beyond auth email
5. Privacy policy must disclose: what data is collected, how long stored, who has access, encryption methods
6. Minimize data collection — don't log IP addresses or device fingerprints unnecessarily
7. Data Processing Agreement (DPA) with all third parties (Stripe, hosting, analytics)
8. Appoint Data Protection Officer if processing over 250 users
9. Geo-block EU if unable to achieve GDPR compliance

**Warning signs:**
- Conversation logs in plaintext database
- No data deletion feature
- Privacy policy is generic template
- Analytics tracking without consent banner
- No DPA with Stripe or hosting provider
- User emails in server logs

**Phase to address:**
Phase 1 (Authentication) and Phase 2 (Chat) — Before storing any user data

---

### Pitfall 6: Inadequate Chargeback Prevention Leading to Payment Processor Termination

**What goes wrong:**
Adult content businesses have 3-5x higher chargeback rates than standard e-commerce. Once chargebacks exceed 1% of transactions, payment processors issue warnings. At 2%, account termination is likely. Each chargeback costs $15-25 + lost revenue.

**Why it happens:**
- Billing descriptor doesn't clearly identify business (causes "I don't recognize this charge")
- No email receipt sent immediately after charge
- Refund policy unclear or too restrictive
- Customer support unresponsive to refund requests
- Free trial doesn't clearly communicate when billing starts
- Users forget they subscribed (especially with adult content)

**How to avoid:**
1. **Clear billing descriptor** — "IntimateAI.chat" not "DigitalOcean" or generic processor name
2. Send email receipt immediately after charge with:
   - What they purchased
   - Subscription duration
   - How to cancel
   - Customer support contact
3. Generous refund policy — 7-day money-back guarantee reduces chargebacks
4. Respond to refund requests within 24 hours
5. Pre-charge email reminder 3 days before trial ends
6. Cancel link in every email
7. Customer support contact prominently displayed
8. Track chargeback reason codes and address root causes

**Warning signs:**
- Chargeback rate above 0.5%
- Payment processor emails about dispute rate
- Multiple "unrecognized charge" disputes
- Billing descriptor is unclear
- No automated email receipts
- Users complaining they can't cancel

**Phase to address:**
Phase 2 (Payments Integration) — Before processing first transaction

---

### Pitfall 7: Telegram Bot API Rate Limiting and Account Bans

**What goes wrong:**
Telegram bans bot account for spam or API abuse. Users lose access to premium feature. Account recovery requires weeks of support tickets. Reputation damage if users perceive service as unreliable.

**Why it happens:**
- Exceeding rate limits (30 messages/second to same chat, 20 messages/minute globally)
- Sending unsolicited messages (users didn't initiate conversation)
- Users report bot as spam
- Bot sends identical messages to multiple users (detected as spam)
- No handling of 429 "Too Many Requests" responses

**How to avoid:**
1. **Implement rate limiting queue** — max 20 messages/minute globally
2. Track per-chat rate limits — max 1 message/second per user
3. Handle 429 responses with exponential backoff
4. Only send messages in response to user input (no unsolicited broadcasts)
5. Provide clear /stop command
6. Track user reports and pause bot for repeat reporters
7. Vary message content — don't send identical messages to multiple users
8. Use message batching for story responses (3-5 messages max, not 13)
9. Monitor bot health with Telegram's getMe API

**Warning signs:**
- 429 error responses in logs
- Users complaining about message delays
- Bot account suspended temporarily
- Identical messages sent to multiple users
- No rate limiting implementation
- Message queue grows unbounded

**Phase to address:**
Phase 3 (Telegram Integration) — Before enabling premium Telegram access

---

### Pitfall 8: Stripe Webhook Security Bypass

**What goes wrong:**
Attacker forges webhook events to grant themselves premium access without payment. All users get free access if webhook signature verification is missing. Revenue loss and payment processor flags suspicious activity.

**Why it happens:**
- Webhook endpoint accepts any POST request without verification
- Stripe signature header not validated
- Using webhook secret from test mode in production
- Webhook secret stored in plaintext or committed to Git
- No replay attack prevention (same event processed multiple times)

**How to avoid:**
1. **Always verify Stripe webhook signatures** using stripe.webhook.construct_event()
2. Use separate webhook secrets for test and production modes
3. Store webhook secret in environment variables, never in code
4. Implement idempotency keys to prevent replay attacks
5. Return 200 OK only after successful signature verification
6. Log all webhook events (timestamp, event type, signature verification status)
7. Rate limit webhook endpoint (max 100 requests/minute)
8. Test webhook verification in staging before production

**Warning signs:**
- Webhook endpoint has no signature verification
- Same webhook secret in test and production
- Webhook secret in docker-compose.yml (CONCERNS.md line 99-106)
- No idempotency tracking
- Webhook processes duplicate events
- Subscription status updated without payment confirmation

**Phase to address:**
Phase 2 (Payments Integration) — Day 1 of webhook implementation

---

### Pitfall 9: Trial Abuse Without Proper Email Verification

**What goes wrong:**
Users create unlimited accounts with disposable emails to get infinite 2-hour trials. No legitimate conversions. Revenue near zero. Database fills with fake accounts. Email sending quota exhausted.

**Why it happens:**
- No email verification required before trial access
- Disposable email domains not blocked
- No device fingerprinting or IP tracking
- Magic link never expires
- Trial hours counted from signup, not first use

**How to avoid:**
1. **Email verification required** before trial starts — send magic link, require click
2. Block disposable email domains (10minutemail, guerrillamail, temp-mail, etc.)
3. Magic link expires after 15 minutes
4. Trial hours countdown starts from first message, not signup
5. Track device fingerprints (canvas, WebGL, audio) and flag duplicates
6. IP-based rate limiting — max 3 signups per IP per day
7. Require credit card for trial (even if not charged) — Stripe payment method storage
8. Monitor trial-to-paid conversion rate (should be >5%)

**Warning signs:**
- Trial conversion rate below 3%
- Many signups with disposable email patterns
- Same IP creating multiple accounts
- Magic links used days after generation
- Trial usage patterns identical across accounts
- Database full of never-verified accounts

**Phase to address:**
Phase 1 (Authentication) — Before enabling trial access

---

### Pitfall 10: Inadequate Session Management Allowing Account Hijacking

**What goes wrong:**
JWT tokens never expire or use weak signing. Attacker steals token and gains permanent access to paid account. User changes password but attacker remains logged in. Session fixation attacks.

**Why it happens:**
- JWT tokens with no expiration time
- Weak JWT secret or hardcoded secret
- No token refresh mechanism
- No session invalidation on password change
- JWT secret in docker-compose.yml or committed to Git
- No logout functionality that actually invalidates tokens

**How to avoid:**
1. **Short-lived access tokens** — 15 minute expiration
2. Long-lived refresh tokens — 7 day expiration, stored in database
3. Rotate JWT secret monthly using environment variable
4. Invalidate all sessions when password changes (clear refresh tokens)
5. Implement proper logout — delete refresh token from database
6. Use httpOnly, secure, sameSite cookies for token storage
7. Monitor for token reuse after logout (indicates compromise)
8. Rate limit auth endpoints (10 requests/minute per IP)

**Warning signs:**
- JWT tokens never expire
- Same JWT secret in test and production
- JWT secret in version control
- No session invalidation on password change
- Logout doesn't actually end session
- No token refresh mechanism

**Phase to address:**
Phase 1 (Authentication) — Before implementing JWT tokens

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| In-memory conversation history | No database setup, faster dev | Lost on restart, can't scale horizontally | Never — conversation persistence is core feature |
| Bare except clauses | Prevents crashes | Silent failures, impossible debugging | Never — use specific exceptions |
| No webhook signature verification | Faster implementation | Security vulnerability, revenue loss | Never — always verify signatures |
| Skip email verification for trials | Better conversion rates | Trial abuse, spam signups | Never in production — only for internal testing |
| Store JWT secret in docker-compose.yml | Easy deployment | Security breach, all sessions compromised | Never — always use environment variables |
| Use test mode Stripe keys in production | Avoid approval delay | No actual payments processed | Never — complete merchant approval first |
| Skip content moderation | Faster AI responses | Legal liability, illegal content | Never — always filter content |
| Magic links never expire | Better UX (no "link expired" errors) | Account takeover if email compromised | Never — 15 minute expiration maximum |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Stripe Payments | Using same webhook secret for test and production | Separate secrets per environment, never commit to Git |
| Stripe Payments | Not handling subscription.deleted webhooks | Implement webhook for all subscription lifecycle events |
| Stripe Payments | Checking payment status synchronously on page load | Cache subscription status, update via webhooks |
| Telegram Bot API | Not handling 429 rate limit responses | Implement queue with exponential backoff |
| Telegram Bot API | Sending messages without user opt-in | Only respond to user-initiated messages |
| Email (Magic Links) | No unsubscribe link in transactional emails | Include unsubscribe even in auth emails (CAN-SPAM) |
| Email (Magic Links) | Links in plain HTTP | Always use HTTPS for magic link destinations |
| Age Verification API | Trusting client-side verification | Server-side verification with API key, never trust frontend |
| Content Moderation API | Only filtering user input, not AI output | Filter both input AND output |
| PostgreSQL | No connection pooling | Use pgBouncer or SQLAlchemy pooling (max_connections=20) |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| TF-IDF vectorizer on every request | Response latency increases linearly | Cache vectorizer, precompute embeddings | >1000 training examples or >10 req/sec |
| Synchronous Telegram API calls | Bot stops responding during message bursts | Async/await with aiohttp, message queue | >5 concurrent users |
| In-memory conversation history | Bot crashes with "out of memory" | Redis cache with TTL, PostgreSQL for persistence | >100 active users or >10k messages |
| No database connection pooling | "Too many connections" errors | pgBouncer or SQLAlchemy pool (size=20) | >20 concurrent requests |
| No rate limiting on API endpoints | DDoS or accidental abuse crashes server | Token bucket rate limiter per IP and per user | First coordinated attack or bug |
| Conversation logs without pruning | Database grows to 100GB+, queries slow | Auto-delete after 90 days, archive to S3 | After 6 months with 1k users |
| WebSocket without heartbeat | Stale connections consume memory | Ping/pong heartbeat every 30s, timeout after 60s | >500 concurrent connections |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing conversation logs in plaintext | Data breach exposes highly sensitive adult content | AES-256 encryption at rest, TLS in transit |
| No content filtering on AI responses | AI generates illegal content (minors, violence) | Keyword blocklist + content moderation API |
| Email addresses in server access logs | Privacy violation, GDPR non-compliance | Redact PII from logs, log to separate encrypted store |
| Sharing analytics with third parties | Privacy policy violation, GDPR breach | Self-hosted analytics (Plausible, Matomo) or explicit consent |
| No IP-based signup rate limiting | Account creation abuse, trial farming | Max 3 signups per IP per day |
| Publicly accessible S3 buckets | Conversation exports or backups exposed | Private buckets, signed URLs with expiration |
| No CSP headers | XSS attacks steal session tokens | Implement Content-Security-Policy header |
| Missing age verification audit trail | Cannot prove compliance during legal review | Log verification timestamp, method, IP in database |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Age verification before seeing anything | Users leave before understanding value | Landing page with non-adult marketing, then age gate |
| Unclear billing descriptor | Chargebacks from "I don't recognize this" | Descriptor matches landing page branding exactly |
| No trial reminder before charge | Users angry about "surprise" charge | Email 3 days before, 1 day before, on charge day |
| Difficult cancellation process | Chargebacks instead of cancellations | Cancel button on every page, no confirmation required |
| Generic AI personality | Feels like ChatGPT with NSFW enabled | Strong personality voice, consistent character |
| Slow AI responses (5+ seconds) | Users think bot is broken | Typing indicator, response within 2 seconds |
| No conversation memory | Users repeat context every message | Track last 10 messages, reference previous topics |
| Subscription-only access to contact support | Users chargeback instead of requesting refund | Support email visible to all, respond within 24h |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Age verification:** Often missing audit trail — verify verification logs are saved to database with timestamp
- [ ] **Stripe integration:** Often missing webhook signature verification — verify construct_event() is used
- [ ] **Email magic links:** Often missing expiration — verify links expire after 15 minutes
- [ ] **Trial system:** Often missing email verification gate — verify trial starts only after email confirmed
- [ ] **Content filtering:** Often missing AI output filtering — verify both input AND output are filtered
- [ ] **Session management:** Often missing token refresh — verify access tokens expire and refresh mechanism exists
- [ ] **Privacy policy:** Often using generic template — verify adult content, data retention, encryption are addressed
- [ ] **Rate limiting:** Often missing per-user limits — verify both IP and user-based rate limits exist
- [ ] **Conversation history:** Often missing encryption — verify AES-256 encryption at rest
- [ ] **Chargeback prevention:** Often missing email receipts — verify receipt sent immediately after charge
- [ ] **Telegram bot:** Often missing rate limit handling — verify 429 responses trigger backoff
- [ ] **Legal compliance:** Often missing attorney review — verify ToS and Privacy Policy reviewed by lawyer

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Payment processor termination | HIGH | 1. Switch to backup processor (CCBill, SegPay) within 48h. 2. Migrate all subscriptions. 3. Email users with new billing process. Est: 2 weeks downtime, 30% user churn |
| GDPR compliance violation | HIGH | 1. Immediate audit and remediation. 2. Implement missing features (data export, deletion). 3. Report breach within 72h if applicable. 4. Legal counsel. Est: $50k+ legal + dev costs |
| Telegram bot ban | MEDIUM | 1. Appeal via @BotSupport. 2. Create new bot as backup. 3. Migrate users with email notification. Est: 1-2 weeks, 10% user churn for premium feature |
| Age verification bypass discovered | HIGH | 1. Immediate shutdown of public access. 2. Fix verification flow. 3. Legal review. 4. Re-verify all existing users. Est: 3-7 days downtime |
| AI generates illegal content | HIGH | 1. Immediately delete content and ban user. 2. Report to NCMEC if required. 3. Enhance content filters. 4. Review all conversations manually. Est: Legal review required |
| JWT secret leaked | MEDIUM | 1. Rotate secret immediately. 2. Invalidate all sessions. 3. Force all users to re-login. 4. Monitor for unauthorized access. Est: 2-4 hours downtime |
| Trial abuse epidemic | LOW | 1. Implement email verification. 2. Add device fingerprinting. 3. Block disposable email domains. 4. Purge fake accounts. Est: 1 week implementation |
| Chargeback rate exceeds 1% | MEDIUM | 1. Pause new subscriptions. 2. Address root cause (billing descriptor, support response time). 3. Contact processor for extension. Est: 2-4 weeks to reduce rate |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Inadequate payment processor due diligence | Phase 0 (Pre-launch) | Merchant account explicitly approves adult content |
| Non-compliant age verification | Phase 1 (Authentication & Landing) | All pages gated, audit trail in database |
| 18 USC 2257 non-compliance | Phase 0 (Legal Review) | Attorney opinion documented, custodian designated if needed |
| Prompt injection attacks | Phase 2 (Core Chat) | Content moderation API integrated, keyword blocklist active |
| GDPR/CCPA non-compliance | Phase 1 (Authentication) + Phase 2 (Chat) | Encryption at rest, data export/deletion features, privacy policy |
| Chargeback prevention inadequacy | Phase 3 (Payments) | Email receipts, clear billing descriptor, refund policy |
| Telegram rate limiting | Phase 4 (Telegram Integration) | Rate limit queue, 429 handling, health monitoring |
| Stripe webhook security | Phase 3 (Payments) | Signature verification tested, idempotency keys implemented |
| Trial abuse | Phase 1 (Authentication) | Email verification, disposable domain blocking, device fingerprinting |
| Session management vulnerabilities | Phase 1 (Authentication) | Token expiration, refresh mechanism, logout invalidation |

## Domain-Specific Anti-Patterns

| Anti-Pattern | Why Tempting | Why Dangerous | Alternative |
|--------------|--------------|---------------|-------------|
| "We'll add age verification later" | Faster MVP launch | Legal liability from day 1, sets bad precedent | Age gate is first feature, no exceptions |
| "Use ChatGPT API for adult content" | Better AI quality | Violates OpenAI ToS, account ban, no refunds | Local Ollama or providers that allow adult content |
| "Just use standard Stripe account" | Faster approval | Account termination after first transaction | High-risk merchant account, 30+ day wait |
| "Store passwords for easier recovery" | Better support UX | Massive security liability | Magic links only, no password storage |
| "Don't encrypt conversation logs" | Simpler database queries | Data breach is catastrophic for adult content | AES-256 encryption, accept query complexity |
| "Skip webhook signature verification initially" | Faster development | Revenue fraud, free accounts | Signatures are 10 lines of code, do it day 1 |

## Sources

**Project Context:**
- `.planning/PROJECT.md` — Project requirements and constraints
- `.planning/codebase/CONCERNS.md` — Existing technical debt and security issues

**Training Data (Pre-January 2025):**
- Payment processing for adult content (HIGH-RISK category knowledge)
- GDPR/CCPA compliance requirements for sensitive data
- Stripe API best practices and webhook security
- Telegram Bot API rate limits and anti-spam policies
- 18 USC 2257 record-keeping requirements (US federal law)
- Common SaaS authentication pitfalls
- AI content moderation patterns

**Confidence Notes:**
- Unable to verify with current (2026) sources due to tool access limitations
- Stripe policies, legal requirements, and Telegram API limits may have changed since training data cutoff (January 2025)
- Recommendations based on established patterns but should be verified with:
  - Current Stripe Restricted Businesses policy
  - Legal counsel specializing in adult content (18 USC 2257, GDPR, state laws)
  - Telegram Bot API documentation for current rate limits
  - Payment processor (CCBill, Epoch, SegPay) current requirements

**Verification Recommended:**
- Stripe adult content merchant requirements (2026 version)
- 18 USC 2257 applicability to AI-generated content (legal opinion)
- Current GDPR enforcement priorities for adult content
- Telegram Bot API rate limit changes post-2025

---
*Pitfalls research for: Adult AI Companion SaaS*
*Researched: 2026-02-21*
*Confidence: MEDIUM — Comprehensive but requires current source verification*
