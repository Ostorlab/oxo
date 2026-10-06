# Contributing to OXO

Thanks for helping improve OXO. Bug fixes, new features, agents, infrastructure and documentation are all welcome.

## Before you start

- Search the [open issues](https://github.com/Ostorlab/oxo/issues) first. For a bug or a feature, open an issue with
  the [bug report](.github/ISSUE_TEMPLATE/bug_report.md) or [feature request](.github/ISSUE_TEMPLATE/feature_request.md)
  template so we can agree on the approach before you write code.
- **Do not report security vulnerabilities in public issues.** Follow [SECURITY.md](SECURITY.md) and email
  `security@ostorlab.co`.
- Building a new agent? Agents live in their own repositories. See the
  [agent documentation](https://oxo.ostorlab.co/docs) and the [Agents Store](https://oxo.ostorlab.co/store).

## Development setup

OXO targets Python 3.13 and 3.14. Docker is needed for the tests marked `docker`.

```shell
git clone https://github.com/Ostorlab/oxo.git
cd oxo
pip install -e ".[testing]"
```

## Checks to run before opening a pull request

CI runs the same checks on every pull request.

```shell
# Tests (CI skips the docker and nats markers)
pytest -m "not docker and not nats"

# Lint and format
ruff check .
ruff format --check

# Type checking
pip install -r typing_requirements.txt
mypy src/ostorlab/agent/schema src/ostorlab/agent/kb src/ostorlab/agent/message src/ostorlab/utils \
  src/ostorlab/apis/runners src/ostorlab/agent/mixins/agent_report_vulnerability_mixin.py src/ostorlab/assets
```

## Code conventions

The full guide is in [AGENTS.md](AGENTS.md). In short:

- Absolute imports only (`from ostorlab.package import module`), grouped standard library, third-party, local.
- Type annotations on all public functions, checked by mypy.
- Custom exceptions inherit from `ostorlab.exceptions.OstorlabError`.
- Tests live under `tests/`, mirror the source layout, use the `*_test.py` suffix and are named
  `test[Action]_[conditionCamelCase]_[expectedResultCamelCase]`.
- CLI commands use `click` and live in `src/ostorlab/cli/`.

## Pull requests

- Keep each pull request focused on one change and add tests for new behavior.
- The title must follow the semantic format checked by CI and start with `feature:`, `fix:` or `documentation:`, for
  example `fix: handle multiple IPs in docker swarm init`.
- Link the issue it resolves and describe how you tested it.

Pull requests are squashed when merged. OXO is maintained by [Ostorlab](https://ostorlab.co).
