# Testing Patterns

**Analysis Date:** 2026-02-20

## Test Framework Status

**Current State:**
- No active test framework configured for Python code
- JavaScript test framework present for GSD tools (Node.js built-in `test` module)
- Python testing framework commented out in dependencies
- NO tests found for the main codebase (`multi_personality_bot.py`, `personalities/` package)

**Available Framework:**
- JavaScript: Node.js built-in `test` module (used in `.claude/get-shit-done/bin/gsd-tools.test.cjs`)
- Python: Pytest recommended but not installed (commented in `requirements.txt`)

## JavaScript Testing Setup

**Framework:**
- Node.js built-in `test` module (no external dependency)
- Assertion library: Node.js built-in `assert` module
- Test location: `.claude/get-shit-done/bin/gsd-tools.test.cjs`

**Run Commands:**
```bash
node .claude/get-shit-done/bin/gsd-tools.test.cjs    # Run tests
# No watch mode or coverage commands detected
```

## Test File Organization

**Location:**
- Co-located with code: `.claude/get-shit-done/bin/gsd-tools.test.cjs` alongside `gsd-tools.cjs`

**Naming:**
- Pattern: `[filename].test.cjs` for CommonJS test files
- Extension: `.cjs` for CommonJS (not TypeScript or ES modules)

**Structure:**
- Single test file for entire tool suite
- Multiple `describe()` blocks for feature grouping
- Individual `test()` blocks within each describe

## Test Structure (JavaScript)

**Suite Organization:**
```javascript
describe('history-digest command', () => {
  beforeEach(() => {
    tmpDir = createTempProject();
  });

  afterEach(() => {
    cleanup(tmpDir);
  });

  test('empty phases directory returns valid schema', () => {
    const result = runGsdTools('history-digest', tmpDir);
    assert.ok(result.success, `Command failed: ${result.error}`);
    // assertions...
  });

  test('nested frontmatter fields extracted correctly', () => {
    // test setup and execution
  });
});
```

**Patterns Observed:**
- `describe()` blocks group related tests
- `beforeEach()` creates temporary test environment
- `afterEach()` cleans up temporary files
- Each `test()` has descriptive name in present tense
- Tests follow Arrange-Act-Assert pattern

## Test Helpers and Fixtures

**Test Utilities:**
```javascript
// Helper to run gsd-tools command
function runGsdTools(args, cwd = process.cwd()) {
  try {
    const result = execSync(`node "${TOOLS_PATH}" ${args}`, {
      cwd,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return { success: true, output: result.trim() };
  } catch (err) {
    return {
      success: false,
      output: err.stdout?.toString().trim() || '',
      error: err.stderr?.toString().trim() || err.message,
    };
  }
}

// Create temp directory structure
function createTempProject() {
  const tmpDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'gsd-test-'));
  fs.mkdirSync(path.join(tmpDir, '.planning', 'phases'), { recursive: true });
  return tmpDir;
}

function cleanup(tmpDir) {
  fs.rmSync(tmpDir, { recursive: true, force: true });
}
```

**Test Data:**
- Temporary directories created with structured layout
- File content fixtures created inline within tests
- YAML frontmatter content as string fixtures

## Assertion Patterns

**Framework:** Node.js `assert` module

**Common Assertions:**
```javascript
assert.ok(result.success, `Command failed: ${result.error}`);
// Check boolean truthy/falsy

assert.deepStrictEqual(digest.phases, {}, 'phases should be empty object');
// Check deep equality with custom message

assert.strictEqual(digest.decisions.length, 2, 'Should have 2 decisions');
// Check strict equality

assert.ok(digest.phases['01'], 'Phase 01 should exist');
// Check object key existence
```

## Mocking Patterns

**Approach:**
- NO mocking framework detected (not using Jest, Sinon, or similar)
- Tests use subprocess execution to test full tool behavior
- File system operations are real, not mocked (temporary directories used)

**Strategy:**
- **Integration testing approach:** Run actual command-line tool
- **Isolation via temporary files:** Each test uses isolated `tmpDir`
- **Subprocess execution:** Tests invoke actual tool via `execSync`

## Test Types (JavaScript Only)

**Tests Present:**
1. **Integration Tests:** Run full `gsd-tools` commands and verify output
   - `history-digest` command tests
   - `phases list` command tests
   - `roadmap get-phase` command tests

2. **File System Tests:** Create test files and verify tool parsing
   - Frontmatter extraction tests
   - YAML field parsing tests
   - File format compatibility tests

3. **Edge Cases:** Malformed files, missing fields, backward compatibility
   - Malformed SUMMARY.md handling
   - Backward compatibility with flat `provides` field
   - Inline array syntax support

## Python Testing

**Current Status:**
- NO tests implemented for Python code
- `pytest>=7.0.0` commented out in `requirements.txt` (line 11)
- No test files found in `personalities/` directory
- No test files found for `multi_personality_bot.py`

**Recommended Setup (if implemented):**
```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov                    # Coverage report
pytest -k test_name             # Run specific test
pytest --watch                  # Watch mode (requires pytest-watch)
```

**Expected Test Locations:**
- `personalities/test_base_personality.py`
- `personalities/test_hotwife_dominant.py`
- `test_multi_personality_bot.py`
- Or co-located: `multi_personality_bot_test.py`

## Coverage

**JavaScript Tests:**
- No coverage tool configured or detected
- Code coverage not measured

**Python:**
- No coverage tool configured
- Recommended: `pytest-cov` if testing were enabled

## Test Quality Observations

**Strengths:**
- Clear test names describing what is being tested
- Good use of helper functions to reduce duplication
- Proper setup/teardown for isolation
- Descriptive assertion messages for debugging

**Gaps:**
- Python code has zero test coverage
- No unit tests for personality system
- No tests for bot response generation logic
- No tests for personality switching mechanism
- No tests for error handling scenarios
- No mocking of external API calls (Telegram, Ollama)

## Critical Untested Areas

**Python Code - High Priority:**
Files: `multi_personality_bot.py`, `personalities/base_personality.py`, `personalities/hotwife_dominant.py`

- Response mode detection (`detect_response_mode()`)
- Personality-enhanced response generation (`create_personality_enhanced_responses()`)
- Training data loading and fallback handling
- Error handling in try-except blocks (bare `except:` clauses)
- TF-IDF similarity matching
- Personality switching and command handling
- Confirmation request flow

**Bot Behavior - No Tests:**
- Message chunking and sequential sending
- Typing indicator functionality
- User state management (pending confirmations, user modes)
- API failures and retries

**Personality System - No Tests:**
- Personality instantiation and defaults
- Scenario type detection
- Random selection from content lists
- Personality-specific confirmation styles
- Response modifier application
- Flair addition consistency

## Test Infrastructure

**Required Tools Not Installed:**
```bash
# For Python testing
pytest>=7.0.0                  # Test runner (commented out)
pytest-cov                     # Coverage plugin (not listed)
pytest-mock                    # Mocking plugin (not listed)

# For code quality
black>=22.0.0                  # Code formatter (commented out)
flake8>=5.0.0                  # Linter (commented out)
```

**Build/CI:**
- No CI/CD pipeline configured (GitHub Actions not set up)
- No test configuration files (no `pytest.ini`, `setup.cfg`, `tox.ini`)
- No pre-commit hooks for test execution

---

*Testing analysis: 2026-02-20*
