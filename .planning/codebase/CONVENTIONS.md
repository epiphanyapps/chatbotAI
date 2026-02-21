# Coding Conventions

**Analysis Date:** 2026-02-20

## Naming Patterns

**Files:**
- Module files: lowercase with underscores (e.g., `multi_personality_bot.py`, `base_personality.py`)
- Class files: lowercase snake_case matching primary class name (e.g., `hotwife_dominant.py` for `HotwifeDominantPersonality`)
- Package directories: lowercase (e.g., `personalities/`)

**Functions:**
- All lowercase with underscores: `detect_response_mode()`, `get_confirmation_style()`, `load_training_data()`
- Verb-first pattern for action functions: `get_`, `set_`, `create_`, `handle_`, `add_`, `find_`
- Boolean/query functions: `get_` prefix rather than `is_`
- Private methods: single underscore prefix (e.g., `_register_personalities()`)

**Variables:**
- All lowercase with underscores: `user_modes`, `training_data`, `conversation_history`
- Dictionary keys: lowercase with underscores (e.g., `user_id`, `scenario_type`, `character_names`)
- Class instance variables: defined in `__init__()` with `self.` prefix
- Constants: UPPERCASE with underscores (e.g., `TELEGRAM_TOKEN`, `OLLAMA_URL`, `MODEL_NAME`)

**Types/Classes:**
- PascalCase for all class names: `MultiPersonalityIntimateBot`, `HotwifePersonalityBase`, `PersonalityManager`, `HotwifeDominantPersonality`
- Abstract base classes: suffix with `Base` (e.g., `PersonalityBase`, `HotwifePersonalityBase`)
- Manager/coordinator classes: suffix with `Manager` (e.g., `PersonalityManager`)

## Code Style

**Formatting:**
- Python 3.x (indicated by `#!/usr/bin/env python3` shebang)
- No explicit formatter configured (not detected in codebase)
- Indentation: 4 spaces (standard Python)
- Line length: No explicit limit enforced

**Linting:**
- No linter configuration detected (no `.eslintrc`, `.flake8`, `pylintrc`)
- Code follows general PEP 8 conventions informally

**Imports:**
- Standard library imports at top
- Third-party imports (`requests`, `sklearn`, `numpy`)
- Local imports (relative imports for personality system)
- Grouped by origin but not strictly separated

## Import Organization

**Order:**
1. Shebang (`#!/usr/bin/env python3`)
2. Module docstring
3. Standard library imports (`json`, `requests`, `time`, `logging`, `random`, `os`)
4. Third-party imports (`sklearn`, `numpy`)
5. Local relative imports (`from personalities import ...`)

**Path Aliases:**
- Relative imports for local modules: `from .base_personality import PersonalityBase`
- Environment-based configuration path: `os.getenv('TRAINING_DATA_PATH', 'training_data.json')`

## Error Handling

**Patterns:**
- Bare `except:` for general failures (lines 48, 60, 341, 352 in `multi_personality_bot.py`)
- Specific `except Exception as e:` for exceptions requiring details (line 176)
- Errors logged but not re-raised: silent failures with fallback values
- No custom exception classes defined

**Fallback Strategy:**
- Configuration errors: Return empty/default values
  - File not found: `return [{"you": "sample input", "her": "sample response"}]`
  - TF-IDF setup failure: Continue with initialization, log error
  - API call failures: Return `False` or `None`
- Response generation: Fallback responses per mode (lines 180-187)

**Network Errors:**
- API calls wrapped in try-except with timeout parameter
- Failures return `False` without raising exceptions
- No retry logic implemented

## Logging

**Framework:** Python `logging` module

**Configuration:** (line 27)
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
```

**Patterns:**
- Module-level logger: `logger = logging.getLogger(__name__)`
- All logging calls use logger instance, not direct `print()`
- Emoji markers in messages for visual distinction:
  - `🎭` for bot personality operations
  - `📖` for story/response operations
  - `❓` for confirmation requests
  - `🔄` for continuation operations
  - `🔥` for mode activations
  - `📋` for processing updates
  - `🎯` for mode detection
  - `🚀` for startup
  - `⚠️` for warnings
  - `❌` for errors

**Log Levels Used:**
- `INFO`: Operation flow, mode detection, responses being sent
- `ERROR`: Configuration failures, processing errors

**Example Logging Calls:**
```python
logger.info(f"🎭 Multi-Personality Bot - Loaded {len(self.training_data)} training examples")
logger.error(f"Failed to load training data from {training_file}")
logger.info(f"🎯 Detected mode: {mode}")
```

## Comments

**When to Comment:**
- Inline comments explain complex logic or non-obvious decisions
- Comments placed above or beside code they describe
- Comments for trigger lists explaining purpose
- Comments for state tracking explaining what variables hold

**Examples from codebase:**
```python
# Continue triggers - should send more story messages
continue_triggers = [...]

# Personality-aware storytelling triggers
story_triggers = [...]

# Track user preferences for response length
self.user_modes = {}
```

**Docstring Pattern:**
- Module-level docstring: Triple-quoted description of file purpose
- Class docstrings: Triple-quoted class purpose (shown in base classes)
- Function docstrings: Triple-quoted function description (present on most methods)
- One-liner docstrings for simple functions
- Extended docstrings for complex logic

**Example docstrings:**
```python
def load_training_data(self):
    """Load training data - personality-specific data will be loaded separately"""
```

## Function Design

**Size:** Functions range from 5-50 lines, with most clustering around 15-25 lines

**Parameters:**
- User input functions typically receive: `user_input`, `user_id` (for context/personalization)
- Helper functions receive: specific data needed (e.g., `scenario_type`, `partner_type`)
- No excessive parameter passing; state held in instance variables
- Optional parameters use defaults (e.g., `partner_type='male'`)

**Return Values:**
- Many functions return strings (responses, messages)
- Some functions return tuples: `(success, message)` or `(text, bool)`
- Some functions return dictionaries or lists
- Helper functions often return single values
- No consistent type hints (not used in codebase)

**Method Organization:**
- Initialization: `__init__()` method
- Public interface: `get_*()` and `handle_*()` methods
- Private helpers: `_register_personalities()` with underscore prefix
- Abstract methods in base classes: marked with `@abstractmethod` decorator

## Module Design

**Exports:**
- `__init__.py` files explicitly define `__all__` lists (see `personalities/__init__.py`)
- Modules import specific classes: `from .base_personality import PersonalityBase, HotwifePersonalityBase`
- Personality manager centralized in package `__init__.py`

**Barrel Files:**
- `personalities/__init__.py` acts as barrel file:
  - Re-exports base classes
  - Defines and exports `PersonalityManager`
  - No wildcard imports used

**Package Structure:**
- Base classes in separate files: encourages inheritance clarity
- Manager class co-located with imports for convenience
- Clear dependency tree: concrete classes depend on abstract base

## Dictionary and Data Structures

**Configuration Dictionaries:**
- Nested dictionaries for personality-specific content
- Keys are lowercase with underscores
- Lists stored within dictionaries for ordered variations

**Example structure:**
```python
self.confirmation_styles = {
    'date_planning': [...],
    'bull_selection': [...],
    'size_comparison': [...]
}

self.character_names = {
    'male_partners': [...],
    'female_friends': [...],
    'husband_terms': [...]
}
```

**Data Access:**
- Direct dictionary access when key is guaranteed
- `get()` method with defaults when key might not exist
- Random selection from lists using `random.choice()`

---

*Convention analysis: 2026-02-20*
