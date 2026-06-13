# Architecture Research

**Domain:** Real-time AI chat SaaS with multi-channel support (Web + Telegram)
**Researched:** 2026-02-21
**Confidence:** MEDIUM

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │ Web Browser  │         │   Telegram   │                  │
│  │  (React UI)  │         │    Client    │                  │
│  └──────┬───────┘         └──────┬───────┘                  │
│         │ WebSocket              │ Bot API                   │
├─────────┼────────────────────────┼──────────────────────────┤
│         │   CHANNEL ADAPTERS     │                           │
│  ┌──────▼───────┐         ┌──────▼───────┐                  │
│  │   WebSocket  │         │   Telegram   │                  │
│  │   Handler    │         │  Bot Handler │                  │
│  └──────┬───────┘         └──────┬───────┘                  │
│         │                        │                           │
│         └────────────┬───────────┘                           │
├──────────────────────┼───────────────────────────────────────┤
│      BUSINESS LOGIC LAYER          │                         │
│  ┌───────────────────▼──────────────────────────┐            │
│  │       Unified Message Router                 │            │
│  │  (Channel-agnostic message handling)         │            │
│  └───────────┬──────────────────────────────────┘            │
│              │                                               │
│  ┌───────────▼──────────────────────────────────┐            │
│  │      Personality Engine                      │            │
│  │  (TF-IDF matching + personality layer)       │            │
│  └───────────┬──────────────────────────────────┘            │
│              │                                               │
│  ┌───────────▼──────────────────────────────────┐            │
│  │      Session & Subscription Manager          │            │
│  │  (Auth, trials, subscription validation)     │            │
│  └──────────────────────────────────────────────┘            │
├─────────────────────────────────────────────────────────────┤
│                    DATA LAYER                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │PostgreSQL│  │  Redis   │  │Training  │  │ Sessions │    │
│  │  (Users, │  │(Sessions,│  │   Data   │  │  (Redis) │    │
│  │   Msgs)  │  │ Pub/Sub) │  │  (JSON)  │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **WebSocket Handler** | Accept connections, maintain session, route messages | FastAPI WebSocket endpoint with ConnectionManager |
| **Telegram Bot Handler** | Receive webhook/polling events, send responses | python-telegram-bot library |
| **Unified Message Router** | Channel-agnostic message processing, coordinate responses | Abstract message handler with channel adapters |
| **Personality Engine** | TF-IDF matching, personality enhancement, response generation | Existing `multi_personality_bot.py` logic extracted |
| **Session Manager** | JWT validation, subscription checks, trial enforcement | FastAPI dependencies + Redis store |
| **Connection Manager** | Track active WebSocket connections, broadcast capability | In-memory dict (single instance) or Redis pub/sub (multi-instance) |
| **Message Store** | Persist conversation history, retrieve context | PostgreSQL with user_id + channel indexing |

## Recommended Project Structure

```
src/
├── api/                      # FastAPI application
│   ├── websocket/            # WebSocket endpoints
│   │   ├── connection.py     # ConnectionManager class
│   │   ├── handlers.py       # WebSocket route handlers
│   │   └── events.py         # Connect/disconnect events
│   ├── auth/                 # Authentication
│   │   ├── magic_link.py     # Email-based auth
│   │   ├── session.py        # JWT token management
│   │   └── dependencies.py   # FastAPI Depends() for auth
│   ├── subscriptions/        # Stripe integration
│   │   ├── stripe.py         # Stripe client wrapper
│   │   ├── webhooks.py       # Payment event handlers
│   │   └── trials.py         # Trial enforcement logic
│   └── main.py               # FastAPI app initialization
│
├── channels/                 # Channel adapters
│   ├── base.py               # Abstract channel interface
│   ├── web.py                # WebSocket channel adapter
│   └── telegram.py           # Telegram channel adapter
│
├── core/                     # Business logic (channel-agnostic)
│   ├── router.py             # Unified message router
│   ├── personality.py        # Personality engine (extracted from bot)
│   ├── matching.py           # TF-IDF response matching
│   └── session.py            # Session state management
│
├── models/                   # Data models
│   ├── user.py               # User, subscription models
│   ├── message.py            # Message models
│   └── session.py            # Session models
│
├── db/                       # Database layer
│   ├── postgres.py           # PostgreSQL connection
│   ├── redis.py              # Redis connection
│   └── repositories/         # Data access layer
│       ├── users.py
│       ├── messages.py
│       └── sessions.py
│
├── personalities/            # Existing personality system
│   ├── base_personality.py   # (keep existing)
│   ├── hotwife_dominant.py   # (keep existing)
│   └── __init__.py           # (keep existing)
│
└── web/                      # Frontend (React)
    ├── src/
    │   ├── components/       # React components
    │   │   ├── Chat/         # Chat UI components
    │   │   ├── Auth/         # Login/signup components
    │   │   └── Subscription/ # Payment components
    │   ├── hooks/            # Custom React hooks
    │   │   ├── useWebSocket.ts  # WebSocket connection hook
    │   │   └── useAuth.ts       # Auth state hook
    │   ├── services/         # API clients
    │   │   ├── websocket.ts  # WebSocket client
    │   │   └── api.ts        # REST API client
    │   └── App.tsx           # Main app component
    └── package.json
```

### Structure Rationale

- **channels/:** Abstract channel adapters allow adding new channels (Discord, WhatsApp) without changing core logic. Web and Telegram both implement the same interface.
- **core/:** Business logic is channel-agnostic. The router receives normalized messages from any channel and coordinates response generation.
- **api/:** FastAPI-specific HTTP/WebSocket handling kept separate from business logic for testability.
- **personalities/:** Existing personality system preserved as-is. Core logic depends on this abstraction.
- **web/:** Frontend lives in same repo for monorepo simplicity at this scale. Can be split later if needed.

## Architectural Patterns

### Pattern 1: Channel Adapter Pattern

**What:** Abstract interface for message channels with concrete implementations for each platform.

**When to use:** Multi-channel chat systems where the same bot serves Web, Telegram, Discord, etc.

**Trade-offs:**
- **Pros:** Core logic stays channel-agnostic, easy to add new channels, centralized personality/subscription logic
- **Cons:** Slight abstraction overhead, need to normalize channel-specific features

**Example:**
```python
# channels/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class NormalizedMessage:
    user_id: str
    text: str
    channel: str
    metadata: dict

@dataclass
class NormalizedResponse:
    text: str
    typing_delay: float = 0

class ChannelAdapter(ABC):
    @abstractmethod
    async def send_message(self, user_id: str, response: NormalizedResponse):
        """Send message through this channel"""
        pass

    @abstractmethod
    async def send_typing_indicator(self, user_id: str):
        """Show typing indicator"""
        pass

    @abstractmethod
    def normalize_message(self, raw_message) -> NormalizedMessage:
        """Convert channel-specific message to normalized format"""
        pass

# channels/telegram.py
class TelegramAdapter(ChannelAdapter):
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_message(self, user_id: str, response: NormalizedResponse):
        if response.typing_delay > 0:
            await self.send_typing_indicator(user_id)
            await asyncio.sleep(response.typing_delay)
        await self.bot.send_message(chat_id=user_id, text=response.text)

    async def send_typing_indicator(self, user_id: str):
        await self.bot.send_chat_action(chat_id=user_id, action="typing")

    def normalize_message(self, update: Update) -> NormalizedMessage:
        return NormalizedMessage(
            user_id=str(update.effective_user.id),
            text=update.message.text,
            channel="telegram",
            metadata={"update": update}
        )

# channels/web.py
class WebSocketAdapter(ChannelAdapter):
    def __init__(self, connection_manager: ConnectionManager):
        self.manager = connection_manager

    async def send_message(self, user_id: str, response: NormalizedResponse):
        if response.typing_delay > 0:
            await self.send_typing_indicator(user_id)
            await asyncio.sleep(response.typing_delay)
        await self.manager.send_personal_message(
            {"type": "message", "text": response.text},
            user_id
        )

    async def send_typing_indicator(self, user_id: str):
        await self.manager.send_personal_message(
            {"type": "typing", "status": "started"},
            user_id
        )

    def normalize_message(self, ws_message: dict) -> NormalizedMessage:
        return NormalizedMessage(
            user_id=ws_message["user_id"],
            text=ws_message["text"],
            channel="web",
            metadata=ws_message
        )
```

### Pattern 2: WebSocket Connection Manager with Redis Pub/Sub

**What:** Manage WebSocket connections across multiple server instances using Redis as message broker.

**When to use:** Production deployment with multiple server instances behind load balancer. Single instance can use in-memory dict.

**Trade-offs:**
- **Pros:** Scales horizontally, messages reach users regardless of which server they're connected to
- **Cons:** Added Redis dependency, slightly increased latency, need to handle Redis disconnections

**Example:**
```python
# api/websocket/connection.py
from fastapi import WebSocket
import redis.asyncio as aioredis
import json

class ConnectionManager:
    def __init__(self, redis_url: str = None):
        # Local connections on this server instance
        self.active_connections: dict[str, WebSocket] = {}

        # Redis pub/sub for multi-instance broadcast
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None

    async def connect(self, user_id: str, websocket: WebSocket):
        """Accept connection and subscribe to user's Redis channel"""
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # Subscribe to user-specific channel for messages from other instances
        if self.redis_client:
            await self.pubsub.subscribe(f"user:{user_id}")

    async def disconnect(self, user_id: str):
        """Remove connection and unsubscribe from Redis"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]

        if self.redis_client:
            await self.pubsub.unsubscribe(f"user:{user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user (handles multi-instance)"""
        # If user connected to this instance, send directly
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

        # Otherwise, publish to Redis for other instances
        elif self.redis_client:
            await self.redis_client.publish(
                f"user:{user_id}",
                json.dumps(message)
            )

    async def listen_redis(self):
        """Background task: listen for messages from other instances"""
        if not self.pubsub:
            return

        async for message in self.pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                user_id = message["channel"].decode().split(":")[1]

                if user_id in self.active_connections:
                    websocket = self.active_connections[user_id]
                    await websocket.send_json(data)

# Usage in FastAPI
manager = ConnectionManager(redis_url="redis://localhost:6379")

@app.on_event("startup")
async def startup():
    manager.redis_client = await aioredis.from_url(manager.redis_url)
    manager.pubsub = manager.redis_client.pubsub()
    asyncio.create_task(manager.listen_redis())

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Process message through unified router
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
```

### Pattern 3: Unified Message Router

**What:** Single entry point for all messages from all channels. Coordinates personality engine, subscription checks, and response delivery.

**When to use:** Multi-channel architectures where business logic should be channel-agnostic.

**Trade-offs:**
- **Pros:** DRY principle, consistent behavior across channels, single place for subscription/trial logic
- **Cons:** Need to carefully design normalized message format to avoid losing channel-specific features

**Example:**
```python
# core/router.py
from channels.base import ChannelAdapter, NormalizedMessage, NormalizedResponse
from core.personality import PersonalityEngine
from core.session import SessionManager
from db.repositories.messages import MessageRepository

class UnifiedMessageRouter:
    def __init__(
        self,
        personality_engine: PersonalityEngine,
        session_manager: SessionManager,
        message_repo: MessageRepository
    ):
        self.personality = personality_engine
        self.sessions = session_manager
        self.messages = message_repo
        self.channel_adapters: dict[str, ChannelAdapter] = {}

    def register_channel(self, channel_name: str, adapter: ChannelAdapter):
        """Register a channel adapter (web, telegram, etc.)"""
        self.channel_adapters[channel_name] = adapter

    async def route_message(self, message: NormalizedMessage):
        """Main routing logic for all incoming messages"""

        # 1. Validate session and subscription
        session = await self.sessions.get_session(message.user_id)
        if not session or not await self.sessions.is_active(session):
            return await self._send_subscription_required(message)

        # 2. Check trial expiration
        if session.is_trial and await self.sessions.trial_expired(session):
            return await self._send_trial_expired(message)

        # 3. Store incoming message
        await self.messages.save(
            user_id=message.user_id,
            text=message.text,
            channel=message.channel,
            direction="incoming"
        )

        # 4. Generate response through personality engine
        responses = await self.personality.generate_response(
            user_id=message.user_id,
            user_input=message.text,
            context=session.conversation_context
        )

        # 5. Send responses through appropriate channel
        adapter = self.channel_adapters[message.channel]
        for response in responses:
            await adapter.send_message(message.user_id, response)

            # Store outgoing message
            await self.messages.save(
                user_id=message.user_id,
                text=response.text,
                channel=message.channel,
                direction="outgoing"
            )

    async def _send_subscription_required(self, message: NormalizedMessage):
        adapter = self.channel_adapters[message.channel]
        response = NormalizedResponse(
            text="Please subscribe at https://intimateai.chat to continue chatting."
        )
        await adapter.send_message(message.user_id, response)
```

## Data Flow

### Request Flow (Web Chat)

```
User types message in browser
    ↓
WebSocket sends JSON: {type: "message", text: "...", user_id: "..."}
    ↓
WebSocket Handler receives raw message
    ↓
WebSocketAdapter.normalize_message() → NormalizedMessage
    ↓
UnifiedMessageRouter.route_message()
    ├─→ SessionManager.is_active() → Check subscription/trial
    ├─→ MessageRepository.save() → Store to PostgreSQL
    ├─→ PersonalityEngine.generate_response()
    │       ├─→ TF-IDF matching against training data
    │       ├─→ Personality enhancement (Sophia's flair)
    │       └─→ Return NormalizedResponse[]
    └─→ WebSocketAdapter.send_message()
            ├─→ Send typing indicator
            ├─→ Delay for realism
            └─→ Send message via WebSocket
```

### Request Flow (Telegram)

```
User sends message in Telegram
    ↓
Telegram Bot API webhook POST
    ↓
Telegram Handler receives Update object
    ↓
TelegramAdapter.normalize_message() → NormalizedMessage
    ↓
UnifiedMessageRouter.route_message()
    [Same flow as web from here]
    ↓
TelegramAdapter.send_message()
    ├─→ Send typing action via Bot API
    ├─→ Delay for realism
    └─→ Send message via Bot API
```

### State Management

```
Session State (Redis)
    ↓ (user_id key)
{
  user_id: "...",
  jwt_token: "...",
  subscription_status: "active" | "trial" | "expired",
  trial_started_at: timestamp,
  trial_hours_remaining: 2.0,
  conversation_context: {
    recent_messages: [...],
    detected_mode: "short" | "long" | "story",
    pending_confirmation: null | {...}
  }
}
    ↑
SessionManager loads/saves
    ↑
UnifiedMessageRouter checks before processing
```

### Key Data Flows

1. **Authentication Flow (Magic Link):**
   - User enters email → API sends magic link → User clicks link → API validates token → Creates session in Redis → Returns JWT → Frontend stores JWT → WebSocket connects with JWT

2. **WebSocket Connection Flow:**
   - Frontend connects to `/ws/{user_id}?token={jwt}` → WebSocket handler validates JWT → Checks subscription status → Accepts connection → Adds to ConnectionManager → Subscribes to Redis channel (if multi-instance)

3. **Message Persistence Flow:**
   - Every message (incoming and outgoing) saved to PostgreSQL → Indexed by user_id and channel → Used for conversation history → Can retrieve context for personality engine

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| **0-1k users** | Single DigitalOcean droplet, in-memory ConnectionManager, local PostgreSQL + Redis. No Redis pub/sub needed. |
| **1k-10k users** | Add Redis pub/sub for ConnectionManager, optimize PostgreSQL queries (indexes on user_id + timestamp), add connection pooling, consider vertical scaling to 4GB droplet. |
| **10k-100k users** | Horizontal scaling with load balancer, Redis pub/sub becomes critical, separate database server, add caching layer for training data vectors, monitor WebSocket connection limits (typically 10k-65k per instance). |
| **100k+ users** | Consider message queue (RabbitMQ/Kafka) instead of Redis pub/sub, database read replicas, CDN for static assets, consider migrating to managed Kubernetes, shard users across multiple personality engine instances. |

### Scaling Priorities

1. **First bottleneck: WebSocket connections per instance**
   - **What breaks:** Single server hits OS file descriptor limit (~10k-65k connections depending on config)
   - **Fix:** Horizontal scaling with Redis pub/sub, load balancer with sticky sessions (or session affinity based on user_id hash)

2. **Second bottleneck: PostgreSQL writes (message persistence)**
   - **What breaks:** High message volume overwhelms single PostgreSQL instance
   - **Fix:** Batch writes (buffer messages for 100ms, bulk insert), add write replicas, consider separating hot data (recent messages) from cold storage (archive older conversations)

3. **Third bottleneck: TF-IDF vector computation**
   - **What breaks:** Calculating similarity for every message becomes CPU-bound
   - **Fix:** Pre-compute and cache vectors for training data (already vectorized), consider moving to approximate nearest neighbor search (Faiss/Annoy) for larger training sets

## Anti-Patterns

### Anti-Pattern 1: Channel-Specific Logic in Core

**What people do:** Put Telegram-specific or WebSocket-specific code in the personality engine or router.

**Why it's wrong:** Makes it impossible to add new channels without modifying core logic. Breaks single responsibility principle. Creates tight coupling.

**Do this instead:** Always use channel adapters. Core logic only operates on `NormalizedMessage` and returns `NormalizedResponse`. Channel adapters handle the translation.

**Example of wrong approach:**
```python
# DON'T DO THIS
async def generate_response(self, update: Update):  # Telegram-specific!
    user_id = update.effective_user.id
    await update.message.reply_text("...")  # Directly using Telegram API
```

**Correct approach:**
```python
# DO THIS
async def generate_response(self, message: NormalizedMessage) -> List[NormalizedResponse]:
    # Channel-agnostic processing
    return [NormalizedResponse(text="...")]
```

### Anti-Pattern 2: Storing Connections in Database

**What people do:** Try to persist WebSocket connections to PostgreSQL or use database to track "online" users.

**Why it's wrong:** WebSocket connections are ephemeral and must be in-memory. Database writes on every connect/disconnect are wasteful. Connection objects aren't serializable.

**Do this instead:** Keep connections in-memory (ConnectionManager). Use Redis for cross-instance coordination. Database only stores durable user data (messages, subscriptions).

### Anti-Pattern 3: Synchronous Blocking in WebSocket Handlers

**What people do:** Call synchronous functions (database queries, file I/O) directly in WebSocket message handlers.

**Why it's wrong:** Blocks the event loop, preventing other connections from being processed. Can cause cascading timeouts.

**Do this instead:** Always use async/await. Ensure database clients are async (asyncpg, motor). Use `asyncio.to_thread()` for unavoidable blocking calls.

**Example:**
```python
# DON'T DO THIS
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    data = await websocket.receive_text()
    result = blocking_db_call()  # BLOCKS EVENT LOOP!
    await websocket.send_text(result)

# DO THIS
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    data = await websocket.receive_text()
    result = await async_db_call()  # Non-blocking
    await websocket.send_text(result)
```

### Anti-Pattern 4: Sending WebSocket Messages from Background Tasks Without Error Handling

**What people do:** Background tasks send messages to WebSocket connections that may have closed.

**Why it's wrong:** Raises `WebSocketDisconnect` exceptions that crash the background task. Connection may close between check and send.

**Do this instead:** Always wrap WebSocket sends in try/except, remove disconnected users from tracking.

**Example:**
```python
# Background task sending typing indicators
async def simulate_typing(user_id: str):
    await asyncio.sleep(1)
    try:
        await manager.send_personal_message({"type": "typing"}, user_id)
    except WebSocketDisconnect:
        await manager.disconnect(user_id)  # Clean up
    except Exception as e:
        logger.error(f"Error sending typing indicator: {e}")
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **Stripe** | Webhook handler + SDK | Subscribe to `customer.subscription.*` events. Verify webhook signatures. Use Stripe-managed subscriptions, update local DB when events fire. |
| **Email (Magic Link)** | SMTP or SendGrid/Mailgun | Send magic link with short-lived JWT (15 min expiry). Use transactional email service for reliability. |
| **Telegram Bot API** | Webhook or long polling | Webhook preferred for production (requires HTTPS). Use `python-telegram-bot` library with async support. |
| **Redis** | Direct async client | Use `redis.asyncio` for pub/sub and caching. Connection pooling built-in. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| **WebSocket ↔ Router** | Method call (async) | WebSocket handler calls `router.route_message()` directly. Same process. |
| **Telegram ↔ Router** | Method call (async) | Telegram handler calls `router.route_message()` directly. Same process. |
| **Router ↔ Personality Engine** | Method call (async) | Router calls `personality.generate_response()`. Same process. No need for events/queues at this scale. |
| **Router ↔ Database** | Repository pattern | Router uses repository classes (users, messages, sessions) for data access. Abstracts SQL details. |
| **ConnectionManager ↔ Redis** | Pub/Sub | Multi-instance deployments use Redis channels for cross-instance communication. Single instance can skip Redis. |

## Build Order Recommendations

Based on component dependencies, suggested build order for web chat milestone:

### Phase 1: Foundation (Week 1)
1. **Database models** - User, Message, Session tables in PostgreSQL
2. **Session Manager** - JWT creation, validation, storage in Redis
3. **Magic Link Auth** - Email sending, token validation, session creation

**Why first:** Everything depends on auth and session management.

### Phase 2: Core Logic Extraction (Week 1-2)
4. **Extract Personality Engine** - Move TF-IDF logic from `multi_personality_bot.py` to `core/personality.py`
5. **Create Channel Adapters** - Base interface and Telegram adapter (wrap existing bot)
6. **Build Unified Router** - Channel-agnostic message routing with subscription checks

**Why second:** Need to refactor existing Telegram bot before adding web channel. Router needs personality engine.

### Phase 3: WebSocket (Week 2)
7. **ConnectionManager** - In-memory connection tracking (single instance version)
8. **WebSocket Handler** - FastAPI endpoint with auth dependency
9. **WebSocket Adapter** - Implement channel adapter interface for web

**Why third:** WebSocket depends on router and session manager being ready.

### Phase 4: Frontend (Week 2-3)
10. **React Chat UI** - Message display, input, typing indicators
11. **WebSocket Client** - Connection management, reconnection logic
12. **Auth Flow UI** - Magic link request, token handling

**Why fourth:** Frontend depends on backend WebSocket API being functional.

### Phase 5: Integration (Week 3)
13. **Message Persistence** - Save all messages (both channels) to PostgreSQL
14. **Conversation Context** - Load recent history for personality engine
15. **Trial Enforcement** - Time-based trial expiration checks

**Why fifth:** Polish features that make the product usable.

### Phase 6: Multi-Instance Support (Later/Optional)
16. **Redis Pub/Sub** - Add to ConnectionManager for horizontal scaling
17. **Load Balancer Config** - Nginx or DigitalOcean load balancer setup

**Why last:** Optimization for scale. Not needed for initial launch or low user counts.

## Implementation Notes

### Existing Codebase Integration

**What to preserve:**
- `personalities/` directory - entire personality system works as-is
- Training data structure - TF-IDF matching logic is solid
- Response modes (short/long/story) - user preference system

**What to refactor:**
- Move TF-IDF matching from `multi_personality_bot.py` to `core/matching.py`
- Extract personality-enhanced response generation to `core/personality.py`
- Wrap existing Telegram bot in `TelegramAdapter` class
- Move session state from in-memory dicts to Redis

**What to add:**
- Entire `api/` directory for FastAPI + WebSocket
- Entire `web/` directory for React frontend
- `channels/base.py` and `channels/web.py`
- `core/router.py` for unified routing
- Database repositories in `db/repositories/`

### Technology Choices Validated

| Technology | Status | Notes |
|------------|--------|-------|
| **FastAPI** | ✓ Confirmed | Official docs show robust WebSocket support via Starlette |
| **Redis pub/sub** | ✓ Confirmed | Standard pattern for multi-instance WebSocket broadcasting |
| **python-telegram-bot** | ✓ Keep existing | Already working, wrap in adapter |
| **PostgreSQL** | ✓ Confirmed | LISTEN/NOTIFY can also work but pub/sub is simpler |
| **React** | ✓ Assumed | Standard for web chat UIs, need frontend research for specifics |

### Open Questions for Frontend Research

- WebSocket reconnection strategies (exponential backoff, max retries)
- React state management (Context API vs Zustand vs Redux)
- Optimistic UI updates (show message immediately vs wait for confirmation)
- Typing indicator debouncing
- Message rendering performance (virtualization for long histories)

## Sources

**HIGH Confidence:**
- FastAPI WebSocket documentation - https://fastapi.tiangolo.com/advanced/websockets/
  - Verified ConnectionManager pattern, WebSocket dependency injection, error handling

**MEDIUM Confidence:**
- Broadcaster library (archived) - https://github.com/encode/broadcaster
  - Confirms Redis pub/sub pattern for multi-instance WebSockets
  - Project archived Aug 2025, but pattern is standard across ecosystems

**LOW Confidence (Training Data):**
- Multi-channel architecture patterns - Based on common SaaS architectures, not verified with current sources
- Scaling thresholds - Based on typical WebSocket connection limits, actual limits vary by OS/config
- React frontend specifics - Needs dedicated frontend research

---
*Architecture research for: IntimateAI web chat frontend*
*Researched: 2026-02-21*
