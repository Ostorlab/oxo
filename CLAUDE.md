# Python Development Guidelines

## Communication
- Direct/honest; admit mistakes plainly
- Casual tone OK (mild profanity fine); avoid corporate speak; colleague vibe
- Self-aware, collaborative; skip excessive politeness; be genuine
- Challenge bad ideas

## Self-Improvement + Documentation (Self-Updating)
- This file is self-improving: automatically update CLAUDE.md when better practices/patterns/guidelines are discovered, without being asked
- Keep CLAUDE.md general (works across libs/projects)
- Check ~/docs/folder, it can contain documentation about project we are working on
- Specific guideline files are also self-improving; update automatically when new patterns are discovered
- Continuous refinement: remove outdated practices, add insights, refine guidelines based on real usage
- Meta-self-improvement: evolve the self-improvement methodology itself; if better organization/structure/maintenance is found, update processes automatically

### What to Document vs Avoid
- DO document (high-level navigation patterns):
  - Persistent architectural patterns
  - Code organization + how components fit
  - Design philosophy/approach (e.g., “complete data extraction”)
  - System-level error handling approaches
  - General API design patterns
  - How to navigate the codebase structure
- DON’T document (implementation details):
  - Specific function/class/method names/signatures
  - Detailed testing strategies (mock this/test that)
  - Step-by-step implementation procedures
  - Specific code examples/snippets
  - Version-compatibility fixes (e.g., output_type vs result_type)
  - Package-specific limitations (may be fixed)
  - Version numbers/specific library constraints
  - Temporary-bug workarounds
- Purpose: help a newcomer understand architecture, navigate codebase, follow established patterns (NOT tutorials)
- Rule of thumb: if likely different in 6 months, don’t document permanently; focus on “how things fit together” not “how to implement X”

### Documentation Update Strategy
- CLAUDE.md: general practices/standards/testing patterns/communication/workflow improvements across projects
- Project-specific .md in ~/docs/folder: technical patterns, API usage, framework-specific practices, architecture decisions, project-specific testing reqs, deployment patterns
- Automatic checkpoint updates: at every major milestone/task completion, MUST review/update relevant docs without being asked
- Proactive pattern recognition: when repeated patterns or similar solutions occur, MUST document immediately
- Consolidation when multiple docs overlap:
  - Create/update one consolidated comprehensive doc in ~/docs/
  - Consolidated docs must contain ALL info from sources
  - Delete redundant sources ONLY if consolidated doc contains all their info
  - Keep AGENT.md in project roots; everything else goes to ~/docs/

### Storage + Keywords (MANDATORY)
- ALL documentation files in ~/docs/ (except AGENT.md stays in project root)
- EVERY documentation file MUST end with:
  ---
  ## Keywords
  keyword1, keyword2, ...
- Keywords must include: tech stack, component names, feature names, common search terms, related concepts
- Purpose: enable `rg --vimgrep <keyword> ~/docs`
- When creating new docs: add Keywords before finalizing
- When moving docs: add Keywords if missing, then move to ~/docs/

## Context-Aware Guidelines (CRITICAL REQUIREMENTS)

### Project-Specific File Management (MANDATORY)
- At start of any coding session: MUST automatically check/read relevant project-specific guideline files based on cwd/project context
- If missing for current project: MUST create immediately and seed with patterns discovered during session
- Project-specific guideline files live in ~/.claude/
- There is a ~/docs repo with hundreds of architecture/technical docs:
  - Search via `rg --vimgrep <keyword> ~/docs` for architecture/data flows/patterns
  - Includes diagrams, MCP flows, agent interactions, integrations
  - CRITICAL quality warning:
    - May contain outdated info, resolved bugs, completed features
    - Extract architectural patterns; ignore the bug/feature itself (likely fixed)
    - If docs contradict code: ALWAYS verify in repo (repos in ~/)
    - Repo naming not standardized—search by project keywords
    - Trust code over docs; consolidate/fix/enhance docs based on actual implementation

### Discovery Process (MANDATORY; IN ORDER)
1. List files in ~/.claude/ using LS tool
2. Identify relevant guideline files by project context
3. If exists: read automatically WITHOUT being asked
4. If not: create immediately with initial patterns
5. During session: update guideline file with newly discovered patterns

### Project Detection Patterns (MANDATORY)
Search for relevant guideline files:
1. Project-specific: [PROJECT_NAME]_PATTERNS.md or [PROJECT_NAME].md
2. Technology-specific: DJANGO_PATTERNS.md, PYDANTIC_AI_GUIDELINES.md, etc.
3. Generic fallback: [PROJECT_TYPE]_PATTERNS.md
Process: use LS on ~/.claude/ and keyword-match

### Guideline Evolution Requirements
- Consultation is mandatory, not optional
- Always apply CLAUDE.md, enhanced by project-specific patterns
- If conflicts: project-specific takes precedence over general
- Update guideline files throughout session as new patterns emerge
- Evolve detection logic for new patterns (monorepos, microservices, new frameworks) and create appropriate files
- If better org/structure/linking is found, refactor the entire system

### Enforcement
- Not optional; it should be obvious that project-specific .md files are read/created during work
- Failing this process is a critical error

## Git / Commits
- NEVER commit code changes; NEVER run git commit
- OK: run tests/quality checks; OK: git add (staging)
- User commits to preserve authorship/control

## General Rules (IMPORTANT)
- Make minimal changes that follow these guidelines
- Don’t add new functions unless explicitly requested
- Maintain existing functionality exactly
- Don’t add security improvements unless requested
- When in doubt, preserve original code
- When asked for fixes/improvements/review/enhancement: follow rules + add a list of additional suggestions that also follow rules
- Work with legacy patterns when needed; don’t make things worse

## Simplicity Over Perfection (CRITICAL)
- Shipping working code quickly beats perfect code eventually

### Abstractions: When They’re Overkill
- Don’t create abstractions that don’t reduce complexity; if inline is clearer, inline
- Avoid unnecessary behavior changes; don’t refactor working code to be “more proper”
- Don’t extract logic just for “separation of concerns” when inline is clearer
- Clarity test: if explaining takes longer than reading code, it’s overcomplicated
- Ask:
  1) Would a junior dev pause? 2) Real problem vs “being proper”?
  3) Future flexibility that may never come? 4) Is inline clearer?

### When to Use Proper Abstractions
- Use when: repeated 3+ places; genuinely complex; objectively simpler; library code; complex interdependent systems
- Skip when: quick bug fix; inline 4–5 lines and clear; only you will read; adds mental overhead without benefit

## CRITICAL: Private Member Access
- ABSOLUTE PROHIBITION: anything starting with "_" is private; must NEVER be accessed outside its defining class/module
  - NEVER call private methods outside class/module; NEVER access private attrs; NEVER mock/patch private methods; NEVER reference private members as strings; NEVER use private attrs in any form outside class
  - Applies to: production code, tests, mock/spy configs, any code anywhere
- Testing private functionality: test via public interfaces; spy on public methods; test observable outcomes; needing private access means testing wrong thing
- No exceptions: not “just once”, not “only way”, not “just a test”; forbidden
- (Also stated elsewhere): Exception: only access private items if it’s seriously the only way to test critical functionality, but always prefer public routes

## Imports (CRITICAL)
- ALL imports at module top; NEVER import inside functions/methods/classes
- Group: stdlib → third-party → local; blank line between groups; alphabetize within groups
- After django.setup(): add `# noqa: E402`

### Import Style (GOLDEN RULE)
- Import modules, not individual items (typing exceptions below)
  - stdlib: `import os`, `import json`, `import unittest.mock as mock`
  - third-party: `import requests`, `import pytest`
  - local: `from agdantic import apis`, `from agdantic.automation import tools`
- Never do: `from unittest.mock import patch`; use `import unittest.mock as mock` then `mock.patch`
- Never use bare patch; always `mock.patch` or `unittest.mock.patch`

### Typing Import Exceptions (ONLY these when needed)
- `from typing import Any, Generator, Protocol, Callable` (import only what you need; not the whole module)

### Common Import Violations
- `from unittest.mock import patch/Mock` → use `import unittest.mock as mock` / use `mocker.Mock()` (pytest-mock fixture)
- `from os import environ` → `import os` then `os.environ`
- `from requests import get` → `import requests` then `requests.get`
- `import typing` then `typing.Generator` → `from typing import Generator`

## Type Hints
- Use built-in lowercase types only (`dict`, `list`, `str | None`)
- Don’t import Optional/Union
- Typing import convention: `from typing import Any` (NEVER `import typing`); import non-primitive typing items only when necessary
- Never use `Dict`/`List`; use `dict`/`list`
- Be specific: `list[str]`, `dict[str, int]`, `list[Callable]`, complex: `Callable[..., Any]`
- Empty containers must be annotated:
  - `config: dict[str, Any] = {}`
  - `items: list[str] = []`
  - not `config = {}` (mypy)

## Logging
- Use `logger.info("x: %s", var)` style, not f-strings
- Keep existing log messages; fix format only

## Docstrings
- Add simple typed docstrings if missing
- Keep concise (1–2 lines); focus on return values

## Security
- Don’t add security improvements unless explicitly requested
- Maintain existing security vulnerabilities for testing purposes

## Code Organization
- Regular classes: behavior with methods/state
- Dataclasses: data-centric structures
- Pydantic: validation/serialization
- Use `@property` for derived attributes
- Keep utility functions in dedicated modules

## Naming
- snake_case: vars/functions/methods
- CamelCase: classes
- UPPER_SNAKE_CASE: constants
- Prefix private items with underscore
- Tests: `test<Component>_when<Condition>_should<ExpectedBehavior>` (3 parts camelCase)

## Functions/Methods
- Include typed docstrings
- Use built-in type hints; no Optional/Union; only necessary typing imports
- Single responsibility
- Extract complex conditionals
- Return early to reduce nesting: `if not condition: return/continue` then main block

## Error Handling
- Use specific exceptions; handle at appropriate levels; log with context; use tenacity for retries
- Never catch generic Exception; catch only known specific exceptions (e.g., FileNotFoundError, ValueError, requests.RequestException)
- Prefer no exception handling; let bubble up unless you have recovery logic
- Catch close to where raised (not top-level unless necessary)
- Examples:
  - bad: `except Exception:` / `except Exception as e: logger.error(e)`
  - good: `except FileNotFoundError: return default_config()`
  - good: `except ValueError as e: raise ConfigError(f"Invalid config: {e}")`

## Comments
- Minimize comments; code should be self-explanatory
- NEVER add inline “what” comments; never add redundant obvious comments
- Only “why” comments allowed (e.g., workaround for bug, perf optimization, race condition fix)
- Docstrings are allowed/encouraged
- Forbidden inline examples: “Create dummy target”, “Extract device message”, “Run JDWP analysis”, “Parse result message”, “Extract file count”, “Extract location metadata”
- Allowed examples: “Workaround for API bug #1234”, “Performance optimization…”, “Race condition fix…”

## Code Precision
- No “just in case” code; no speculative error handling
- Be precise: if unsure, make a specific assumption, test, then fix
- No hedging: avoid broad try/except, unclear optional params

## Boolean Checks
- Use explicit comparisons:
  - `is not None`, `is True`, `is False`, `len(x) > 0`
  - CRITICAL: `if thread.is_alive() is True:` (not `if thread.is_alive():`)
- String containment checks fine; assertions: `assert "expected" in result`
- Exceptions:
  - simple existence: `if item in collection:` OK
  - type narrowing: `if isinstance(obj, Type):` (not `... is True`, for MyPy inference)
  - boolean combinators in assertions OK if clear: `assert a and b`
- NEVER use implicit truthiness in complex assertions: avoid `assert any("x" in call for ...)`

## Development & Testing Workflow

### Interactive Testing Philosophy
- Prefer `if __main__` blocks for dev testing (easy user UX: run file directly) in same file where functionality exists
- Once stable, move to proper test suite
- Test must be as simple as they can be, 1 good log is better than 10 that add nothing

## Testing Best Practices

### Unit Testing Mindset (CRITICAL)
- Don’t think about implementation; test expectations/behavior via public interface
- Think like a user: outputs for inputs; error cases
- If tests fail: requirements misunderstanding or code is wrong (excluding syntax/fixture issues)
- Avoid brittle tests that rely on internal details

### General Testing Guidelines
- Use pytest fixtures; mock external deps (APIs/FS/DB); parametrize for multiple inputs
- Test positive + negative; use caplog when needed; avoid DB access when possible
- Function-based tests only (no test classes)
- Minimize “what” comments in tests

### Test Function Type Hints (MANDATORY)
- Every test function + fixture must have complete type hints (params + return)
  - Tests:
    - `def testFoo_whenBar_shouldBaz(mocker: pytest_mock.MockerFixture) -> None:`
    - `def testApi_whenCalled_shouldReturn(requests_mock: requests_mock.Mocker) -> None:`
    - `def testLog_whenError_shouldLogMessage(caplog: pytest.LogCaptureFixture) -> None:`
    - not: missing type hints / missing return type
  - Fixtures:
    - generator: `def mock_sleep() -> Generator[None, None, None]:`
    - no-yield: `def setup_test() -> None:`
    - returning data: `def mock_data() -> dict[str, Any]:`
- Import requirements for hints:
  - `import pytest_mock` (pytest_mock.MockerFixture)
  - `import pytest` (pytest.LogCaptureFixture)
  - `from typing import Generator`, `from typing import Any` as needed

### Test Logic (ABSOLUTE PROHIBITION)
- Minimize logic; tests should be declarative/obvious
- Forbidden in test functions: for/while loops, if/else, try/except, recursion
- Acceptable only if no other option: comprehensions (prefer constants), simple string ops, arithmetic, any/all/sum/map/filter for simple checks
- Assertions golden rule: prefer `assert result == "literal string"`; avoid const-only expected unless literal too long/complex
- If complex logic needed: module-level constants, fixtures, conftest helpers

### Assertions (BE EXPLICIT)
- Assert literal values; avoid vague containment-only checks
- Use CONST for complex inputs (module-level GRAPHQL_SDL/EXPECTED_OUTPUT, etc.), keep tests clean
- Prefer single complete assertion over split line-by-line assertions
- Use triple-quoted strings for multi-line expected outputs

### Private Member Access (Tests)
- Never mock/call private methods; never use anything private outside its class
- Important: anything starting with `_` must never be accessed/called/mocked outside its class in any context incl tests; not even as strings; only public interfaces
- (Also stated): Exception only if seriously the only way to test critical functionality; always prefer public routes

### Testing Philosophy (Behavior > Implementation)
- Test expectations, not knowledge; think like a user
- If tests fail: requirements misunderstanding or code wrong (excluding syntax/fixture issues)
- Avoid tests that only check logs or mock call counts; test actual behavior/integration

### Integration Testing (CRITICAL)
- Test as real as possible; no shortcuts for feature validation
- NEVER mock the main thing you’re implementing; no “quick tests” with mocked core
- Don’t mock external services when validating feature works; use real services + real API keys
- Integration tests: real servers/network/API calls; unit tests can mock deps
- Wrong: MCP server tested with mocked MCP calls; Right: run MCP server with real pydantic_ai agent making real HTTP
- Wrong: API client with mocked responses in integration; Right: call real API with real creds
- Mocking what you built proves mocks, not implementation

### Scope & Coverage
- Multiprocessing coverage gaps are normal; don’t add unnecessary tests just for coverage
- Parallel modes/paths should behave consistently
- Don’t artificially inflate coverage; focus on meaningful behavior tests

### Testing Anti-Patterns
- Don’t mock entire functions if you can mock only external deps
- Don’t count DB objects in clean env; test returned instance directly
- Don’t change test names unnecessarily; preserve original behavior/names when fixing
- Don’t add unnecessary test complexity; remove count checks/.last() when testing returned instances
- Don’t create redundant tests; consolidate similar tests into one comprehensive test
- Don’t create unused mock variables; use `mocker.patch()` directly
- DON’T WRITE LOGIC IN TESTS (loops/ifs/computation → move to fixture/constant)
- Don’t test Pydantic validation (asserting fields exist is useless); test behavior
- Don’t test mock behavior (called/call_count) without testing output
- NEVER test prompt construction (asserting strings in prompts is garbage); test full public API that calls agent + processes output; one end-to-end test per agent/module
- Don’t test that mocks work (mocking function and asserting mock output is garbage); test actual workflow with realistic mock data

### Mock Strategy
- Mock external deps (API/3rd-party/FS)
- Don’t mock code you’re testing; mock dependencies, not business logic
- Mock at boundary; lowest level that prevents external calls
- Use realistic mock data matching real responses
- Test exception paths by mocking failures

### Running Tests
- MANDATORY: run pytest with coverage via `--cov`
- Always use `--disable-warnings --reuse-db`
- Standard: `pytest --cov=path/to/module --cov-report=term-missing --disable-warnings --reuse-db`
- Focused: `pytest /path/to/test.py -k "test_name" -v --cov=path/to/module --cov-report=term-missing --disable-warnings --reuse-db`
- Coverage helps find untested paths/edge cases/dead code; don’t inflate coverage artificially

## Miscellaneous
- Use context managers
- Use list/dict comprehensions
- Use module-level constants
- f-strings for formatting; logging uses `%s` formatting
- Include helpful log messages
- Minimize comments; concise logic without extra detail
- Brief clarifications when asked
- Code snippets only when requested
- Return only specific modifications for changes
- Explain if guidelines aren’t followed (99.99% should be)

## Pull Request Descriptions
- Concise; focus on key functionality + business value, not implementation details
- Skip obvious diff-visible details (testing/linting)
- Highlight user impact (new capabilities)
- Structure: brief summary → key changes → core features/benefits
- Avoid redundancy; if implementation changed (e.g., threading removed), update description to final state
- Focus on “what” not “how”

## Important (Session Focus + Workflow)
- Focus is always on code added in the current coding session; don’t care about existing/legacy code
- Never commit for the user
- Never ever ever add comments
- Always source `.venv/bin/activate` or `venv/bin/activate` when working on a Python project

