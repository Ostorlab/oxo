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
- **Target Python versions**: 3.9, 3.10, 3.11
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
- Use built-in generics: `list[str]` instead of `List[str]` (Python 3.9+)
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
- Pull requests run CI on Python 3.9, 3.10, 3.11
- Squash commits when merging

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

