# Phase 2: Authentication & Legal Foundation - Research

**Researched:** 2026-02-21
**Domain:** Passwordless authentication, session management, fraud prevention, legal compliance
**Confidence:** HIGH

## Summary

This phase implements passwordless magic link authentication for an adult AI companion SaaS. The core flow involves: user enters email, system sends signed magic link, user clicks link to authenticate, system creates JWT session. Key challenges include preventing trial abuse (disposable emails, device fingerprinting), maintaining secure sessions via Valkey/Redis, and meeting 2026 age verification requirements.

The authentication stack uses FastAPI with PyJWT for sessions, itsdangerous for magic link tokens, Resend for transactional email, and FingerprintJS for device identification. Age verification requires more than a simple checkbox in 2026 - an audit trail of user declarations is the minimum for self-declaration approaches, though stricter verification may be needed depending on jurisdiction.

**Primary recommendation:** Implement magic link auth with 15-minute token expiry, store fingerprints server-side for trial tracking, use Valkey for session storage with 7-day refresh tokens, and create audit-logged age confirmations at each critical point.

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUTH-01 | Magic link email (passwordless) | itsdangerous URLSafeTimedSerializer for tokens, Resend for email delivery, 15-min expiry |
| AUTH-02 | Email verification before trial | Token verification endpoint confirms email ownership before account activation |
| AUTH-03 | 18+ age confirmation with audit trail | Database table logging IP, timestamp, user agent, fingerprint at declaration |
| AUTH-04 | Block disposable email domains | disposable-email-domains PyPI package (3,500+ domains, daily updates) |
| AUTH-05 | Device fingerprinting for trial abuse | FingerprintJS v5 (MIT, client-side) with server-side fingerprint storage |
| AUTH-06 | JWT session management | PyJWT with HS256, 30-min access tokens, 7-day refresh tokens in Valkey |
| LEGAL-01 | Terms of Service page | Static React page with adult-content-specific clauses |
| LEGAL-02 | Privacy Policy page | GDPR/CCPA compliant static page, data collection disclosure |
| LEGAL-03 | Age verification gate | Modal with checkbox + audit logging, blocks access until confirmed |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyJWT | latest | JWT token creation/verification | FastAPI official recommendation (replaced python-jose) |
| itsdangerous | 2.2.x | Magic link token signing with expiry | Pallets project, URL-safe timed tokens |
| resend | latest | Transactional email API | Modern API, FastAPI integration, good deliverability |
| disposable-email-domains | 0.0.162+ | Block throwaway emails | Community-maintained, 3,500+ domains, daily updates |
| valkey-py | latest | Session storage (Redis-compatible) | Fork of redis-py, async support, direct drop-in |
| @fingerprintjs/fingerprintjs | 5.0.1 | Browser device fingerprinting | MIT license, free, client-side fingerprint generation |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pwdlib[argon2] | latest | Password hashing (if needed) | Only if adding password fallback |
| email-validator | latest | Email format validation | Before disposable domain check |
| python-multipart | latest | Form data parsing | Magic link request forms |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Resend | SendGrid | SendGrid cheaper at volume, Resend simpler API |
| FingerprintJS OSS | Fingerprint Pro | Pro is 99.5% accurate vs ~60%, but costs money |
| FingerprintJS OSS | ThumbmarkJS | ThumbmarkJS claims higher accuracy, less mature |
| PyJWT | python-jose | python-jose abandoned, Python 3.10+ incompatible |
| itsdangerous | PyJWT for magic links | itsdangerous is simpler for one-time tokens |

**Installation:**
```bash
# Backend
pip install pyjwt itsdangerous resend disposable-email-domains valkey email-validator python-multipart

# Frontend
npm install @fingerprintjs/fingerprintjs
```

## Architecture Patterns

### Recommended Project Structure
```
backend/
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py          # Auth endpoints
│   │   ├── magic_link.py      # Token generation/validation
│   │   ├── jwt_handler.py     # JWT creation/refresh
│   │   ├── email_validator.py # Disposable email checking
│   │   └── fingerprint.py     # Device fingerprint handling
│   ├── legal/
│   │   ├── __init__.py
│   │   └── router.py          # Legal page endpoints
│   ├── core/
│   │   ├── config.py          # Settings (secrets, expiry times)
│   │   ├── security.py        # Token utilities
│   │   └── dependencies.py    # FastAPI dependencies
│   └── models/
│       ├── user.py            # User model
│       └── audit.py           # Age verification audit log
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.tsx          # Magic link request
│   │   ├── VerifyEmail.tsx    # Token verification
│   │   ├── AgeGate.tsx        # 18+ confirmation
│   │   ├── Terms.tsx          # Terms of Service
│   │   └── Privacy.tsx        # Privacy Policy
│   └── utils/
│       └── fingerprint.ts     # FingerprintJS integration
```

### Pattern 1: Magic Link Flow
**What:** User requests login via email, receives signed URL, clicks to authenticate
**When to use:** All authentication (signup and login unified)
**Example:**
```python
# Source: itsdangerous docs + FastAPI patterns
from itsdangerous.url_safe import URLSafeTimedSerializer
from datetime import timedelta

class MagicLinkService:
    def __init__(self, secret_key: str):
        self.serializer = URLSafeTimedSerializer(secret_key)

    def create_token(self, email: str) -> str:
        """Create signed, time-limited token"""
        return self.serializer.dumps({"email": email, "purpose": "login"})

    def verify_token(self, token: str, max_age: int = 900) -> dict | None:
        """Verify token, 15 minutes (900s) default expiry"""
        try:
            return self.serializer.loads(token, max_age=max_age)
        except SignatureExpired:
            return None  # Token expired
        except BadSignature:
            return None  # Invalid token
```

### Pattern 2: JWT Session Management with Valkey
**What:** Short-lived access tokens + long-lived refresh tokens stored in Valkey
**When to use:** All authenticated requests after initial login
**Example:**
```python
# Source: FastAPI docs + valkey-py
import jwt
from datetime import datetime, timedelta, timezone
import valkey

class SessionManager:
    def __init__(self, secret: str, valkey_client: valkey.Valkey):
        self.secret = secret
        self.algorithm = "HS256"
        self.valkey = valkey_client
        self.access_expire = timedelta(minutes=30)
        self.refresh_expire = timedelta(days=7)

    def create_tokens(self, user_id: str) -> dict:
        """Create access + refresh token pair"""
        now = datetime.now(timezone.utc)

        access_token = jwt.encode(
            {"sub": user_id, "exp": now + self.access_expire, "type": "access"},
            self.secret,
            algorithm=self.algorithm
        )

        refresh_token = jwt.encode(
            {"sub": user_id, "exp": now + self.refresh_expire, "type": "refresh"},
            self.secret,
            algorithm=self.algorithm
        )

        # Store refresh token in Valkey for revocation capability
        self.valkey.setex(
            f"refresh:{user_id}:{refresh_token[:8]}",
            int(self.refresh_expire.total_seconds()),
            refresh_token
        )

        return {"access_token": access_token, "refresh_token": refresh_token}
```

### Pattern 3: Device Fingerprinting for Trial Abuse
**What:** Client generates fingerprint, server stores and checks for duplicates
**When to use:** Trial signup, suspicious activity detection
**Example:**
```typescript
// Source: FingerprintJS GitHub
import FingerprintJS from '@fingerprintjs/fingerprintjs';

export async function getVisitorId(): Promise<string> {
  const fp = await FingerprintJS.load();
  const result = await fp.get();
  return result.visitorId;
}

// Send with signup request
const fingerprint = await getVisitorId();
await fetch('/api/auth/signup', {
  method: 'POST',
  body: JSON.stringify({ email, fingerprint })
});
```

```python
# Server-side fingerprint check
async def check_trial_abuse(fingerprint: str, db: AsyncSession) -> bool:
    """Returns True if fingerprint already used trial"""
    result = await db.execute(
        select(User).where(
            User.device_fingerprint == fingerprint,
            User.trial_used == True
        )
    )
    return result.scalar_one_or_none() is not None
```

### Pattern 4: Age Verification with Audit Trail
**What:** Log every age confirmation with full context
**When to use:** Before granting access to adult content
**Example:**
```python
# Source: Legal compliance research
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime

class AgeVerificationAudit(Base):
    __tablename__ = "age_verification_audit"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null for pre-signup
    email = Column(String, nullable=True)
    ip_address = Column(String, nullable=False)
    user_agent = Column(String, nullable=False)
    device_fingerprint = Column(String, nullable=True)
    confirmed_18_plus = Column(Boolean, nullable=False)
    confirmation_text = Column(String, nullable=False)  # Exact text user agreed to
    created_at = Column(DateTime, default=datetime.utcnow)

async def log_age_verification(
    request: Request,
    user_id: int | None,
    email: str | None,
    fingerprint: str | None,
    db: AsyncSession
):
    audit = AgeVerificationAudit(
        user_id=user_id,
        email=email,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "unknown"),
        device_fingerprint=fingerprint,
        confirmed_18_plus=True,
        confirmation_text="I confirm that I am at least 18 years old and legally permitted to access adult content in my jurisdiction."
    )
    db.add(audit)
    await db.commit()
```

### Anti-Patterns to Avoid

- **Storing magic link tokens in database:** Use signed tokens (itsdangerous) that are self-validating. Database storage adds complexity and cleanup burden.
- **Long magic link expiry:** 15 minutes max. Longer creates security risk if email compromised.
- **Trusting client fingerprints blindly:** Fingerprints can be spoofed. Use them as ONE signal, not sole source of truth.
- **Self-declaration checkbox without audit:** In 2026, simple checkboxes without logging are legally insufficient. Always create audit trail.
- **Storing JWTs in localStorage:** Use httpOnly cookies for refresh tokens. Access tokens can be in memory.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Disposable email detection | Regex patterns or manual list | disposable-email-domains package | 3,500+ domains, daily updates, community maintained |
| Magic link tokens | Custom JWT or random strings | itsdangerous URLSafeTimedSerializer | Built-in expiry, URL-safe, signature verification |
| Email delivery | Direct SMTP | Resend API | Deliverability, SPF/DKIM, bounce handling |
| Device fingerprinting | Canvas/WebGL hashing yourself | FingerprintJS | 30+ signals, browser compat, tested edge cases |
| Session storage | File-based or in-memory dict | Valkey (Redis) | Persistence, TTL, distributed, already deployed |

**Key insight:** Authentication has many edge cases (token replay, timing attacks, race conditions). Using established libraries means inheriting years of security fixes.

## Common Pitfalls

### Pitfall 1: Magic Link Token Replay
**What goes wrong:** User can reuse magic link multiple times
**Why it happens:** Token not invalidated after first use
**How to avoid:** Store token hash in Valkey with short TTL, delete on use
**Warning signs:** Multiple sessions created from same link
```python
# Prevention: atomic token consumption
async def consume_token(token: str, valkey: Valkey) -> bool:
    """Returns True if token was valid and consumed, False if already used"""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    # SETNX returns 1 only if key didn't exist
    was_new = await valkey.setnx(f"used_token:{token_hash}", "1")
    if was_new:
        await valkey.expire(f"used_token:{token_hash}", 900)  # 15 min cleanup
    return bool(was_new)
```

### Pitfall 2: Subdomain Disposable Emails
**What goes wrong:** User uses `anything@subdomain.disposable.com`
**Why it happens:** Only checking exact domain match
**How to avoid:** Check all parent domains
**Warning signs:** Users with unusual subdomains
```python
from disposable_email_domains import blocklist

def is_disposable_email(email: str) -> bool:
    domain = email.split("@")[1].lower()
    parts = domain.split(".")
    # Check each possible parent domain
    for i in range(len(parts)):
        check_domain = ".".join(parts[i:])
        if check_domain in blocklist:
            return True
    return False
```

### Pitfall 3: Fingerprint Privacy Concerns
**What goes wrong:** User data collected without consent, GDPR violation
**Why it happens:** Fingerprinting before consent
**How to avoid:** Only fingerprint AFTER user consents to ToS/Privacy Policy
**Warning signs:** Fingerprint data exists for users who never completed signup

### Pitfall 4: JWT Secret Key Exposure
**What goes wrong:** JWT secret committed to repo or hardcoded
**Why it happens:** Quick development, forgetting to move to env vars
**How to avoid:** Generate with `openssl rand -hex 32`, store in DO App Platform secrets
**Warning signs:** JWT_SECRET in any non-env file

### Pitfall 5: Race Condition in Token Verification
**What goes wrong:** Two requests with same token both succeed
**Why it happens:** Check-then-delete pattern has gap
**How to avoid:** Use atomic operations (SETNX in Valkey)
**Warning signs:** Duplicate sessions for same user

### Pitfall 6: Age Verification Bypass
**What goes wrong:** User accesses content without age confirmation
**Why it happens:** Frontend-only checks, no server validation
**How to avoid:** Check age_verified flag in database on EVERY protected request
**Warning signs:** Users with no audit log accessing content

## Code Examples

### Complete Magic Link Request Endpoint
```python
# Source: FastAPI patterns + itsdangerous docs + Resend docs
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from disposable_email_domains import blocklist
import resend

router = APIRouter(prefix="/auth", tags=["auth"])
resend.api_key = os.environ["RESEND_API_KEY"]
magic_link_service = MagicLinkService(os.environ["MAGIC_LINK_SECRET"])

class MagicLinkRequest(BaseModel):
    email: EmailStr
    fingerprint: str

@router.post("/magic-link")
async def request_magic_link(
    request: Request,
    body: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
    valkey: Valkey = Depends(get_valkey)
):
    # 1. Check disposable email
    domain = body.email.split("@")[1].lower()
    if domain in blocklist:
        raise HTTPException(400, "Please use a non-disposable email address")

    # 2. Check fingerprint for trial abuse (if new user)
    existing_user = await get_user_by_email(db, body.email)
    if not existing_user:
        if await check_trial_abuse(body.fingerprint, db):
            raise HTTPException(400, "Trial already used on this device")

    # 3. Rate limit: max 3 requests per email per hour
    rate_key = f"magic_link_rate:{body.email}"
    count = await valkey.incr(rate_key)
    if count == 1:
        await valkey.expire(rate_key, 3600)
    if count > 3:
        raise HTTPException(429, "Too many requests. Please try again later.")

    # 4. Generate token and send email
    token = magic_link_service.create_token(body.email)
    magic_url = f"https://intimateai.chat/verify?token={token}"

    resend.Emails.send({
        "from": "IntimateAI <noreply@intimateai.chat>",
        "to": [body.email],
        "subject": "Your login link",
        "html": f"""
            <p>Click to sign in:</p>
            <a href="{magic_url}">Sign in to IntimateAI</a>
            <p>This link expires in 15 minutes.</p>
        """
    })

    return {"message": "Check your email for the login link"}
```

### Token Verification Endpoint
```python
@router.get("/verify")
async def verify_magic_link(
    token: str,
    fingerprint: str,  # From query param, set by frontend
    request: Request,
    db: AsyncSession = Depends(get_db),
    valkey: Valkey = Depends(get_valkey)
):
    # 1. Atomically consume token (prevent replay)
    if not await consume_token(token, valkey):
        raise HTTPException(400, "Link already used or expired")

    # 2. Verify token signature and expiry
    payload = magic_link_service.verify_token(token)
    if not payload:
        raise HTTPException(400, "Invalid or expired link")

    email = payload["email"]

    # 3. Get or create user
    user = await get_or_create_user(db, email, fingerprint)

    # 4. Create session tokens
    session_manager = SessionManager(
        os.environ["JWT_SECRET"],
        valkey
    )
    tokens = session_manager.create_tokens(str(user.id))

    # 5. Set refresh token as httpOnly cookie
    response = JSONResponse({"access_token": tokens["access_token"]})
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )

    return response
```

### FingerprintJS React Integration
```typescript
// Source: FingerprintJS GitHub README
import { useEffect, useState } from 'react';
import FingerprintJS from '@fingerprintjs/fingerprintjs';

export function useFingerprint() {
  const [visitorId, setVisitorId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadFingerprint = async () => {
      try {
        const fp = await FingerprintJS.load();
        const result = await fp.get();
        setVisitorId(result.visitorId);
      } catch (error) {
        console.error('Fingerprint error:', error);
        // Fallback: generate random ID (less accurate but functional)
        setVisitorId(crypto.randomUUID());
      } finally {
        setLoading(false);
      }
    };
    loadFingerprint();
  }, []);

  return { visitorId, loading };
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| python-jose for JWT | PyJWT | 2024 | python-jose abandoned, incompatible with Python 3.10+ |
| Self-declaration age gates | Audit-logged declarations | 2025-2026 | 25+ US states require verification, checkbox alone insufficient |
| Cookies for sessions | JWTs with httpOnly refresh | 2020+ | Better security, stateless access tokens |
| Manual disposable lists | Community-maintained packages | Ongoing | Daily updates, 3,500+ domains |
| redis-py | valkey-py (compatible) | 2024 | Valkey fork of Redis, same API |

**Deprecated/outdated:**
- python-jose: Abandoned, use PyJWT
- Simple age checkboxes: Legally insufficient in many US states (2026)
- redis-py: Still works but valkey-py is forward-compatible with Valkey

## Open Questions

1. **Fingerprint Pro vs Open Source**
   - What we know: Open source is ~60% accurate, Pro is 99.5%
   - What's unclear: Is 60% sufficient for trial abuse prevention?
   - Recommendation: Start with OSS, upgrade if abuse becomes significant

2. **Age Verification Stringency**
   - What we know: 25+ US states require verification for adult content
   - What's unclear: Does checkbox + audit satisfy regulations for AI chat (vs porn)?
   - Recommendation: Implement checkbox + audit now, add ID verification option later if needed

3. **Email Provider Selection**
   - What we know: Resend has clean API, SendGrid is more established
   - What's unclear: Deliverability for adult content domain
   - Recommendation: Start with Resend, ensure domain warmup and proper SPF/DKIM

## Sources

### Primary (HIGH confidence)
- [FastAPI Official JWT Documentation](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/) - PyJWT recommendation, token structure
- [ItsDangerous Documentation](https://itsdangerous.palletsprojects.com/en/stable/) - URLSafeTimedSerializer usage
- [disposable-email-domains PyPI](https://pypi.org/project/disposable-email-domains/) - Version 0.0.162, usage patterns
- [FingerprintJS GitHub](https://github.com/fingerprintjs/fingerprintjs) - v5.0.1, MIT license, accuracy notes
- [valkey-py GitHub](https://github.com/valkey-io/valkey-py) - redis-py compatibility
- [Resend FastAPI Docs](https://resend.com/docs/send-with-fastapi) - Integration example

### Secondary (MEDIUM confidence)
- [FastAPI JWT Best Practices Discussion](https://github.com/fastapi/fastapi/discussions/11345) - python-jose abandonment
- [Age Verification Laws 2026](https://natlawreview.com/article/new-age-verification-reality-compliance-rapidly-expanding-state-regulatory) - Legal landscape
- [Magic Link Security Best Practices](https://guptadeepak.com/mastering-magic-link-security-a-deep-dive-for-developers/) - Token expiry recommendations

### Tertiary (LOW confidence)
- WebSearch results for adult content ToS requirements - needs legal review
- FingerprintJS accuracy claims from blog posts - needs production testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official docs and maintained packages verified
- Architecture: HIGH - Follows FastAPI official patterns
- Pitfalls: HIGH - Common issues documented in GitHub issues and security guides
- Legal compliance: MEDIUM - Laws vary by jurisdiction, self-declaration may not suffice everywhere

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (30 days - auth patterns stable, legal landscape evolving)
