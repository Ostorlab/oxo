"""Isolate configuration before loading OXO's pytest plugin and test modules."""

import atexit
import os
import tempfile

_TEST_CONFIGURATION = tempfile.TemporaryDirectory(prefix="oxo-pytest-")
os.environ["OSTORLAB_PRIVATE_DIR"] = _TEST_CONFIGURATION.name
atexit.register(_TEST_CONFIGURATION.cleanup)

pytest_plugins = ["ostorlab.testing.agent"]
