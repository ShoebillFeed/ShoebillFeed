"""Keep the suite off the ambient filesystem.

`TTS_MODEL_DIR` defaults to `/data/voices`, which is a volume mount inside
the container and almost never writable anywhere else. Any test reaching
the real `get_engine()` therefore constructs a `PiperEngine`, whose
`__init__` does `os.makedirs(model_dir)` -- which succeeds as root (how
this suite happened to be run locally) and fails with PermissionError as
an ordinary user, which is how CI runs it.

Pointing the setting at a tmp dir for every test fixes that at the root
rather than per-test, so a future test that touches the real engine can't
reintroduce it. Both caches have to be cleared: `get_settings` would
otherwise hand back a Settings built before the env var was set, and
`get_engine` would hand back an engine built from it.
"""

import pytest

from app.config import get_settings
from app.engines.factory import get_engine


@pytest.fixture(autouse=True)
def isolated_model_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TTS_MODEL_DIR", str(tmp_path / "voices"))
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    # Clear on the way out too, so the next test doesn't inherit an engine
    # pointing at this test's now-deleted tmp_path.
    get_settings.cache_clear()
    get_engine.cache_clear()
