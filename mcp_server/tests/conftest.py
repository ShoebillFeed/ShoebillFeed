import importlib.util
import os
import sys
from pathlib import Path

import pytest

SERVER_PATH = Path(__file__).resolve().parent.parent / "server.py"


def _load_server():
    """Import server.py fresh.

    It exits at import time without SHOEBILL_API_TOKEN, and registers its
    tools on a module-level MCPServer -- so each test that filters tools
    needs its own module instance rather than a shared one.
    """
    os.environ.setdefault("SHOEBILL_API_TOKEN", "test-token")
    os.environ.setdefault("SHOEBILL_API_URL", "http://shoebill.test/api")
    spec = importlib.util.spec_from_file_location("shoebill_mcp_server", SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def server():
    """A fresh server module with all HTTP verbs stubbed to fail loudly, so
    a test that forgets to stub one gets a clear error rather than a real
    request."""
    mod = _load_server()

    def _unstubbed(*args, **kwargs):
        raise AssertionError("HTTP call not stubbed in this test")

    mod._get = _unstubbed
    mod._post = _unstubbed
    mod._patch = _unstubbed
    mod._delete = _unstubbed
    return mod


@pytest.fixture
def load_server():
    """For tests that need to control the module before tools are filtered."""
    return _load_server
