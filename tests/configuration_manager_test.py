"""Tests for configuration directory isolation and shared credentials."""

import os
import pathlib
import subprocess
import sys

import pytest

from ostorlab import configuration_manager


def testConfigurationManager_whenExplicitDirectoryProvided_usesRequestedDirectory(
    tmp_path: pathlib.Path,
) -> None:
    """An explicit directory remains independent of the cached default manager."""
    default_manager = configuration_manager.ConfigurationManager()
    private_dir = tmp_path / "explicit"

    manager = configuration_manager.ConfigurationManager(private_dir=private_dir)
    manager.set_authorization_token("explicit-token")

    assert manager is not default_manager
    assert manager.conf_path == private_dir.resolve()
    assert manager.authorization_token == "explicit-token"
    assert (private_dir / "token").is_file()
    assert default_manager.authorization_token != "explicit-token"


def testConfigurationManager_whenDirectoryRepeated_preservesApiKey(
    tmp_path: pathlib.Path,
) -> None:
    """Managers for the same directory share in-memory API key state."""
    manager = configuration_manager.ConfigurationManager(tmp_path)
    manager.api_key = "directory-key"

    repeated_manager = configuration_manager.ConfigurationManager(
        private_dir=tmp_path / "."
    )

    assert repeated_manager is manager
    assert repeated_manager.api_key == "directory-key"


def testConfigurationManager_whenDefaultRepeated_preservesApiKey() -> None:
    """Default callers retain the CLI's configured API key."""
    manager = configuration_manager.ConfigurationManager()
    manager.api_key = "default-key"

    assert configuration_manager.ConfigurationManager() is manager
    assert configuration_manager.ConfigurationManager().api_key == "default-key"


def testConfigurationManager_whenEnvironmentChanges_usesNewDirectory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """An environment override chooses its own cached configuration directory."""
    first_manager = configuration_manager.ConfigurationManager()
    override_dir = tmp_path / "override"
    monkeypatch.setenv("OSTORLAB_PRIVATE_DIR", str(override_dir))

    manager = configuration_manager.ConfigurationManager()

    assert manager.conf_path == override_dir.resolve()
    assert manager is not first_manager


def testConfigurationManager_whenImportedWithEnvironmentOverride_isolatesDatabase(
    tmp_path: pathlib.Path,
) -> None:
    """The environment override applies before the package initializes its DB URL."""
    override_dir = tmp_path / "override"
    environment = dict(os.environ, OSTORLAB_PRIVATE_DIR=str(override_dir))
    code = """
import pathlib
from unittest import mock
with mock.patch.object(pathlib.Path, 'home', return_value=pathlib.Path('fallback')):
    from ostorlab import configuration_manager
    from ostorlab.runtimes.local.models import models
manager = configuration_manager.ConfigurationManager()
manager.set_authorization_token('isolated-token')
print(manager.conf_path)
print(models.ENGINE_URL)
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.splitlines() == [
        str(override_dir),
        f"sqlite:///{override_dir}/db.sqlite",
    ]
    assert (override_dir / "token").is_file()
    assert (tmp_path / "fallback" / ".ostorlab").exists() is False


def testPytestBootstrap_whenInstalledPluginAvailable_isolatesBeforePackageImport(
    tmp_path: pathlib.Path,
) -> None:
    """A standard pytest invocation loads agent fixtures after temporary storage."""
    repository = pathlib.Path(__file__).resolve().parents[1]
    fallback_home = tmp_path / "fallback"
    environment = dict(os.environ, PYTHONPATH=str(repository / "src"))
    environment["OXO_TEST_FALLBACK_HOME"] = str(fallback_home)
    code = """
import importlib
import os
import pathlib
from unittest import mock
import pytest

class BootstrapProbe:
    def pytest_sessionstart(self, session):
        manager_module = importlib.import_module('ostorlab.configuration_manager')
        models = importlib.import_module('ostorlab.runtimes.local.models.models')
        directory = manager_module.ConfigurationManager().conf_path
        assert directory.name.startswith('oxo-pytest-')
        assert models.ENGINE_URL == f'sqlite:///{directory}/db.sqlite'
        assert session.config.pluginmanager.has_plugin('pytest_ostorlab') is False
        assert session.config.pluginmanager.has_plugin('ostorlab.testing.agent')
        print('bootstrap-isolated')

fallback_home = pathlib.Path(os.environ['OXO_TEST_FALLBACK_HOME'])
with mock.patch.object(pathlib.Path, 'home', return_value=fallback_home):
    result = pytest.main([
        'tests/configuration_manager_test.py', '-k', 'whenDefaultRepeated',
        '--no-cov', '-q', '--timeout=30'
    ], plugins=[BootstrapProbe()])
assert (fallback_home / '.ostorlab').exists() is False
raise SystemExit(result)
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "bootstrap-isolated" in result.stdout
    assert fallback_home.exists() is False
