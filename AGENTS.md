# Agents Information Guide for OXO/Ostorlab

This file contains essential information for development agents working on the OXO (Ostorlab) codebase.

## Build, Lint, Test, and Format Commands

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage (configured in setup.cfg)
pytest --cov=ostorlab --cov-report=term-missing

# Run specific test file
pytest tests/path/to/specific_test.py

# Run tests matching a pattern
pytest -k "test_function_name"

# Run tests excluding docker/nats tests (as done in CI)
pytest -m "not docker and not nats"

# Install test dependencies
pip install -e .[testing]
```

### Linting and Formatting
```bash
# Run ruff linter
ruff check .

# Run ruff linter with auto-fix
ruff --fix .

# Run ruff formatter (black-compatible)
ruff format .

# Check formatting without applying changes
ruff format --check

# Run all tox linting/formatting environment
tox -e ruff
```

### Type Checking
```bash
# Run mypy type checking on specific modules (as done in CI)
mypy src/ostorlab/agent/schema
mypy src/ostorlab/agent/kb
mypy src/ostorlab/agent/message
mypy src/ostorlab/utils
mypy src/ostorlab/apis/runners
mypy src/ostorlab/agent/mixins/agent_report_vulnerability_mixin.py
mypy src/ostorlab/assets
mypy src/ostorlab/ai tests/ai

# Install typing dependencies
pip install -r typing_requirements.txt
```

### Other Commands
```bash
# Build package
python -m build .

# Clean build artifacts
rm -rf build dist *.egg-info

# Install all extras
pip install -e ".[testing,scanner,agent,serve]"
```

## Code Style Guidelines

### General Principles
- **Line length**: 88 characters (Black/ruff compatible)
- **Target Python versions**: 3.13, 3.14
- **Code formatter**: Ruff (replaced flake8/black)
- **Type checker**: mypy with strict configuration
- **No comments**: Code should be self-documenting

### Imports
- Use **absolute imports** only: `from ostorlab.package import module`
- Import order: standard library → third-party → local
- Group imports by type with single blank line between groups
- Example:
  ```python
  import dataclasses
  import io
  from typing import List, Optional, Dict, Any
  
  from ostorlab.agent.schema import loader
  from ostorlab.utils import definitions
  ```

### File and Module Structure
- **Layout**: `src/` layout with `src/ostorlab` as main package
- **Test naming**: `*_test.py` suffix (not test_*.py)
- **Source file naming**: lowercase_with_underscores.py
- **Class naming**: PascalCase (e.g., `AgentDefinition`)
- **Function naming**: snake_case (e.g., `from_yaml()`)
- **Variables**: snake_case
- **Constants**: UPPER_SNAKE_CASE

### Error Handling
- Base exception: `OstorlabError` from `ostorlab.exceptions`
- Custom exceptions inherit from `OstorlabError`
- Use specific exception types, not bare `Exception`
- Example:
  ```python
  from ostorlab import exceptions


  class MissingTargetSelector(exceptions.OstorlabError):
      """Missing asset selector definition."""
  ```

### Type Annotations
- **Enforced**: mypy with strict configuration
- All public functions must have type annotations
- Return types must be specified
- Use `Optional[T]` instead of `Union[T, None]`
- Use built-in generics: `list[str]` instead of `List[str]` (Python 3.10+)
- All abstract methods and properties must be typed

### Testing
- Test file location: Mirror source structure under `tests/`
- Test class naming: Not required, use descriptive functions
- Test function naming: `test[Action]_[conditionCamelCase]_[expectedResultCamelCase]`
- Use pytest fixtures defined in `tests/conftest.py`
- Avoid test classes unless necessary for grouping
- Use pytest markers: `docker`, `nats` (skip in CI with `-m "not docker and not nats"`)

### Documentation
- Use Google-style or reStructuredText docstrings
- Module-level docstrings required
- Public functions/classes must have docstrings
- Keep docstrings concise and focused

### Data Classes and Configuration
- Use `@dataclasses.dataclass` for configuration objects
- Provide sensible defaults using `dataclasses.field(default_factory=list)`
- Use `Optional[T]` for nullable fields

### CLI Development
- Use `click` framework for CLI commands
- Keep commands in `ostorlab/cli/` directory
- Use `@click.group()` for command groups
- Provide help text for all commands and options

### Protobuf and Generated Code
- Exclude `*_pb2.py` files from linting/formatting: `ruff.toml` extends-exclude
- Mypy excludes: `exclude = .*_pb2.py`

### Git Workflow
- Use conventional commit messages
- Pull requests run CI on Python 3.13, 3.14
- Squash commits when merging

### AI Models and Providers (`ostorlab.ai`)
- **Agents must not construct `pydantic_ai.providers` or `pydantic_ai.models` themselves; they call
  `factory.build_model("provider/model", credential, options=..., settings=...)`.**
- `ostorlab.ai` is replacing the per-agent builder copies (500–700 lines each) that already diverged
  on Vertex handling, the Azure v1 fallback and per-provider HTTP clients. Existing agents are being
  migrated in follow-up PRs.
- The package never reads agent configuration or environment variables; callers pass every input
  (identifier, credential, gateway URLs, settings) explicitly. Agent-specific
  selection logic (per-role models, complexity routing) stays in the agent.
- Adding a provider means completing every step:
  1. Add a `build_<provider>(request)` builder under `src/ostorlab/ai/providers/`.
  2. Register it in `factory._BUILDERS`.
  3. Add it to `keys.PROVIDER_PRIORITY`.
  4. Add a case to `_BUILD_CASES` in `tests/ai/factory_test.py`.
  5. If the provider can run without a key, add it to `factory._CREDENTIAL_OPTIONAL` and always
     pass the SDK the `NO_API_KEY` placeholder plus the provider's explicit base URL, never `None`,
     so it cannot read either value from the environment.

  The registry coverage tests fail until steps 2–4 are done.
- Request timeouts come from `settings.default_settings(timeout=...)`: pydantic-ai sends
  `ModelSettings.timeout` with every request, overriding any HTTP client timeout.
- `openai_compatible/<model>` targets any server exposing an OpenAI-compatible API (vLLM, LM Studio,
  llama.cpp `llama-server`, LocalAI, Hugging Face TGI (Text Generation Inference)) at a configured URL, with no LiteLLM gateway required. It
  complements `ollama`, which also speaks the OpenAI-compatible API but has its own provider
  (pydantic-ai's `OllamaProvider`, with per-model profiles); `openai_compatible` is the generic path
  for any other server.
- `earthruntime/<model>` (e.g. `earthruntime/deepseek-v4-flash`) targets the open-weight models
  Earth Runtime hosts behind an OpenAI-compatible chat API
  (`EARTHRUNTIME_BASE_URL`, currently the staging endpoint) with the conservative gateway profile,
  like `litellm` and `z_ai`. It requires an API key.
- Every provider requires a credential except `ollama` and `openai_compatible`, the entries in
  `factory._CREDENTIAL_OPTIONAL`. Local servers run with no key; a key for a hosted or secured server
  is the caller's responsibility.
- Builders always pass pydantic-ai an explicit credential and URL. For keyless local servers that
  means the `NO_API_KEY` placeholder plus the required `ollama_base_url` /
  `openai_compatible_base_url`; this is what stops pydantic-ai falling back to `OLLAMA_*` or
  `OPENAI_API_KEY` / `OPENAI_BASE_URL` (which would send a real key to the configured server), so
  keep both.
- Keep credential JSON formats (Bedrock, Azure, Vertex) backwards compatible: they are stored as
  secrets on the platform.
- Errors raise `errors.ModelConfigurationError` (an `OstorlabError` and a `ValueError`) and never
  include the credential in the message.
- The dependencies live in the `agent` extra: `import ostorlab.ai` needs `ostorlab[agent]`,
  which every agent already installs. Plain `pip install ostorlab` stays free of the AI SDKs.
- Keep `anthropic<1.0.0`: anthropic 1.x moved to `httpx2`, which pydantic-ai 1.107's
  `AnthropicProvider` rejects. Lift the cap only once pydantic-ai supports `httpx2`.

## Project Structure Reference

```
/home/asm/PycharmProjects/oxo/
├── src/ostorlab/              # Main source package
│   ├── agent/                 # Agent framework
│   ├── assets/                # Asset definitions
│   ├── cli/                   # Command-line interface
│   ├── scanner/               # Scanner components
│   ├── serve_app/             # Web service components
│   └── utils/                 # Utilities
├── tests/                     # Test package
│   ├── agent/                 # Agent tests
│   ├── assets/                # Asset tests
│   ├── cli/                   # CLI tests
│   └── conftest.py           # Pytest configuration
├── setup.cfg                 # Package configuration
├── ruff.toml                 # Ruff configuration
├── .mypy.ini                 # MyPy configuration
└── tox.ini                   # Tox configuration
```

