# Architecture

**Analysis Date:** 2026-02-20

## Pattern Overview

**Overall:** Layered bot-driven SaaS architecture with modular personality system

**Key Characteristics:**
- **Telegram-first interface** - Primary user interaction point with Telegram Bot API
- **Personality abstraction layer** - Swappable personality modules influencing bot responses
- **Subscription-gated access** - SaaS layer controlling feature access based on user tier
- **TF-IDF similarity matching** - Training data retrieval based on user input vectors
- **Sequential multi-message delivery** - Simulated realistic typing/response patterns

## Layers

**Telegram Bot Layer:**
- Purpose: Handle all user communication via Telegram API, command processing, message delivery
- Location: `multi_personality_bot.py` (lines 1-380)
- Contains: Message handlers, response generation, typing indicators, message chunking
- Depends on: PersonalityManager, TF-IDF vectorizer, training data, Telegram API
- Used by: End users via Telegram client

**Personality System Layer:**
- Purpose: Provide modular personality variations and response modification pipeline
- Location: `personalities/` directory - base classes and personality implementations
- Contains:
  - `base_personality.py` - Abstract base classes (PersonalityBase, HotwifePersonalityBase)
  - `hotwife_dominant.py` - Sophia personality implementation
  - `__init__.py` - PersonalityManager for personality registration and switching
- Depends on: No external dependencies (self-contained)
- Used by: Bot layer for response enhancement and scenario-specific behavior

**Training Data Layer:**
- Purpose: Store and match conversation examples for response selection
- Location: Training data loaded at runtime (referenced as `training_data.json` in code)
- Contains: Input/output pairs structured as `{"you": user_input, "her": response}`
- Depends on: TfidfVectorizer from scikit-learn
- Used by: Bot layer's similarity matching in `find_best_training_response()`

**SaaS Management Layer (Planned):**
- Purpose: Subscription control, payment processing, user session management
- Location: Not yet implemented; documented in SAAS_ARCHITECTURE.md
- Contains: PaymentService, UserService, TrialManager classes (documented but not coded)
- Depends on: Stripe API, PostgreSQL, Redis
- Used by: All layers for access control and session validation

**Infrastructure Layer:**
- Purpose: Hosting, containerization, networking, SSL/TLS termination
- Location: `docker-compose.yml`, `terraform/` directory, `nginx/` directory
- Contains: Docker services, Terraform modules, nginx configuration
- Depends on: DigitalOcean provider, Docker runtime, nginx
- Used by: DevOps for deployment and infrastructure management

## Data Flow

**User Message Processing Flow:**

1. **Input Reception**: User sends message via Telegram → Telegram API delivers to bot endpoint
2. **Command Detection**: `handle_commands()` checks if message is bot command
   - If command: Route to personality command handler or standard command (lines 189-235)
   - If not command: Continue to response generation
3. **Mode Detection**: `detect_response_mode()` analyzes input and user state (lines 64-118)
   - Checks for continue/story/long response triggers
   - Determines response mode: `'short'`, `'long'`, `'storytelling'`, `'continue_story'`
4. **Personality Retrieval**: `personality_manager.get_personality(user_id)` gets current personality
5. **Response Generation**: Based on mode and pending confirmation state (lines 237-296)
   - **Story Mode**: Request confirmation first, store in `pending_confirmations`
   - **Continue Mode**: Generate story responses directly
   - **Normal Mode**: Generate single response
6. **Training Data Matching**: `find_best_training_response()` (lines 158-178)
   - TF-IDF vectorize user input
   - Calculate cosine similarity with training data vectors
   - Select top matches based on mode
   - Random selection from good matches (similarity > 0.05)
7. **Personality Enhancement**: `create_personality_enhanced_responses()` (lines 143-156)
   - Apply personality-specific modifications via `get_response_modifiers()`
   - Add personality flair via `add_personality_flair()`
8. **Delivery**: `send_message_chunks()` dispatches response with typing indicators
9. **Sequential Delivery** (story mode): `send_sequential_story_responses()` sends multiple messages with delays (1-5 seconds between)

**State Management:**
- User conversation history: Stored in memory `conversation_history` dict (line 37)
- User preference modes: Stored in `user_modes` dict (line 38) - persists during bot session
- Pending confirmations: Stored in `pending_confirmations` dict (line 39) - tracks users awaiting confirmation responses
- Current personality: Per-user personality instance stored in `PersonalityManager.current_personality` dict (line 21 in `__init__.py`)

## Key Abstractions

**PersonalityBase (Abstract):**
- Purpose: Define contract for all personality implementations
- Examples: `base_personality.py` line 10, implemented by `HotwifeDominantPersonality`
- Pattern: Abstract base class with @abstractmethod decorators defining:
  - `get_personality_name()` - Returns personality display name
  - `get_confirmation_style(scenario_type)` - Returns scenario-specific confirmation templates
  - `get_story_themes()` - Returns list of story themes for this personality
  - `get_response_modifiers(base_response)` - Modifies base response to match personality
  - `add_personality_flair(text)` - Adds personality-specific language markers

**HotwifePersonalityBase (Intermediate):**
- Purpose: Shared functionality for hotwife market personalities
- Examples: Base for Sophia (HotwifeDominantPersonality)
- Pattern: Extends PersonalityBase with market-specific methods:
  - `get_bull_reference()` - Random bull terminology
  - `get_cuckold_reference()` - Random cuckold terminology
  - `get_size_reference()` - Random size comparison terminology
  - Pre-configured scenario types and commands

**HotwifeDominantPersonality (Concrete):**
- Purpose: Sophia personality - confident, assertive, dominant hotwife
- Examples: `personalities/hotwife_dominant.py`
- Pattern: Concrete implementation with personality identity, character names, locations, confirmation templates, response modifiers
- Characteristics:
  - Traits: confident, sexually_assertive, dominant, direct, experienced (line 19-22)
  - Character names: Male partners (Marcus, Tyrone, Jake...), female friends, husband terms (line 26-37)
  - Key phrases organized by scenario: size_comparisons, date_announcements, dominance_assertions, affectionate_dominance (lines 52-81)
  - Confirmation templates for scenario types: date_planning, bull_selection, size_comparison (lines 84-103)

**PersonalityManager (Singleton-like):**
- Purpose: Manage multiple personalities, switching, availability based on subscription
- Examples: `personalities/__init__.py` lines 16-103
- Pattern: Registry pattern for personality classes
  - `_register_personalities()` - Initialize personality catalog (line 27-45)
  - `get_personality(user_id)` - Lazy initialization per user (line 47-51)
  - `switch_personality(user_id, personality_name)` - Switch current personality (line 53-61)
  - `get_available_personalities(user_subscription)` - Filter by subscription tier (line 63-74)

**TF-IDF Response Matching:**
- Purpose: Find best training data response matching user input
- Examples: `multi_personality_bot.py` lines 45-47, 158-178
- Pattern: Vectorization + cosine similarity
  - Initialize: `TfidfVectorizer(max_features=1000, stop_words=None)` on training inputs (line 45)
  - Query: Transform user input, calculate cosine similarity with stored vectors
  - Selection: Filter by similarity threshold (0.05), select from top 3-8 matches based on mode
  - Fallback: Return mode-specific fallback response if no good matches (line 174)

## Entry Points

**Telegram Bot Handler:**
- Location: `multi_personality_bot.py` (implicit, full file is entry point)
- Triggers: Telegram API webhook or long polling with user messages and commands
- Responsibilities:
  - Initialize personality system and training data (lines 31-52)
  - Route incoming messages to command or response generation handlers (implied in run() at line 364)
  - Coordinate with personality manager for all user interactions

**Command Handler:**
- Location: `multi_personality_bot.py::handle_commands()` (lines 189-235)
- Triggers: User message starting with `/`
- Responsibilities:
  - Route personality system commands (`/personality`, `/date_planning`, etc.) to PersonalityManager (lines 193-200)
  - Handle standard bot commands: `/short`, `/long`, `/story`, `/auto`, `/help` (lines 203-233)
  - Return command response or None if not handled

**Response Generator:**
- Location: `multi_personality_bot.py::generate_and_send_response()` (lines 237-296)
- Triggers: Non-command user messages OR confirmation responses
- Responsibilities:
  - Detect response mode (story, continue, long, short)
  - Manage pending confirmation workflow
  - Route to personality-enhanced response generation
  - Send responses with typing indicators and natural delays

**Personality Command Handler:**
- Location: `personalities/__init__.py::PersonalityManager.handle_personality_command()` (lines 81-103)
- Triggers: Commands like `/personality`, `/date_planning`, `/bull_selection`
- Responsibilities:
  - Handle personality switching via `/personality <name>`
  - Route scenario-specific commands to current personality
  - Return personality-specific response

## Error Handling

**Strategy:** Graceful degradation with fallback responses

**Patterns:**

1. **TF-IDF Vectorization Failure** (lines 46-49):
   ```python
   try:
       self.tfidf_matrix = self.vectorizer.fit_transform(self.inputs)
   except:
       logger.error("Failed to setup TF-IDF")
   ```
   Logs error but continues; matching will fail later and trigger fallback

2. **Training Data Load Failure** (lines 56-62):
   ```python
   try:
       with open(training_file, 'r', encoding='utf-8') as f:
           return json.load(f)
   except:
       logger.error(f"Failed to load training data from {training_file}")
       return [{"you": "sample input", "her": "sample response"}]
   ```
   Returns minimal fallback training data

3. **Similarity Matching Failure** (lines 176-178):
   ```python
   except Exception as e:
       logger.error(f"Training matching error: {e}")
       return self.get_fallback_response(mode)
   ```
   Falls back to mode-specific canned responses

4. **Message Sending Failure** (lines 336-342, 345-353):
   ```python
   except:
       pass  # Silent failure on Telegram API errors
   ```
   Non-critical failures (typing indicator, messaging) silently skip

## Cross-Cutting Concerns

**Logging:** Basic Python logging (lines 26-28)
- Level: INFO
- Format: `'%(asctime)s - %(levelname)s - %(message)s'`
- Used for startup info, mode detection, confirmation tracking
- Example: `logger.info(f"🎯 Detected mode: {mode}")` (line 260)

**Validation:** Implicit input validation
- Command validation: Check if command string matches known patterns
- Mode validation: Fallback triggers for unmatched modes
- Response validation: Similarity threshold (0.05) ensures quality matches

**Authentication:** Not implemented in current bot layer
- Noted for future SaaS layer: User subscription checks documented in SAAS_ARCHITECTURE.md
- Current implementation: No per-user authentication or authorization

**Session Management:** In-memory per-session
- Tracked via `user_id` key in dicts
- Persists only during bot runtime
- State lost on bot restart

---

*Architecture analysis: 2026-02-20*
