import importlib.util
import sys
import types
from pathlib import Path


def _load_downloader_module():
    if "loguru" not in sys.modules:
        logger_stub = types.SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda *a, **k: None,
        )
        sys.modules["loguru"] = types.SimpleNamespace(logger=logger_stub)

    if "celery" not in sys.modules:
        sys.modules["celery"] = types.SimpleNamespace(shared_task=lambda *a, **k: (lambda f: f))
    if "celery.exceptions" not in sys.modules:
        sys.modules["celery.exceptions"] = types.SimpleNamespace(MaxRetriesExceededError=Exception)

    module_path = Path(__file__).resolve().parents[1] / "athena" / "tasks" / "downloader.py"
    spec = importlib.util.spec_from_file_location("downloader_proxy_test_module", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeScalarResult:
    def __init__(self, row):
        self._row = row

    def scalar_one_or_none(self):
        return self._row


class _FakeDb:
    def __init__(self, row=None, should_raise=False):
        self._row = row
        self._should_raise = should_raise

    def execute(self, _stmt):
        if self._should_raise:
            raise RuntimeError("db error")
        return _FakeScalarResult(self._row)


class _Row:
    def __init__(self, proxy_enabled: bool, proxy_url: str | None):
        self.proxy_enabled = proxy_enabled
        self.proxy_url = proxy_url


def test_proxy_resolution_uses_db_proxy_when_enabled():
    module = _load_downloader_module()
    db = _FakeDb(row=_Row(True, "http://proxy.local:8080"))
    assert module._resolve_runtime_proxy_url(db, "http://fallback:9000") == "http://proxy.local:8080"


def test_proxy_resolution_returns_none_when_disabled():
    module = _load_downloader_module()
    db = _FakeDb(row=_Row(False, "http://proxy.local:8080"))
    assert module._resolve_runtime_proxy_url(db, "http://fallback:9000") is None


def test_proxy_resolution_fallback_on_db_error():
    module = _load_downloader_module()
    db = _FakeDb(should_raise=True)
    assert module._resolve_runtime_proxy_url(db, "http://fallback:9000") == "http://fallback:9000"
