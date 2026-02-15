import importlib.util
import sys
import types
from pathlib import Path


def _load_arxiv_module():
    managed_keys = [
        "loguru",
        "httpx",
        "feedparser",
        "athena.adapters.base",
        "athena.core.config",
    ]
    originals = {key: sys.modules.get(key) for key in managed_keys}

    if "loguru" not in sys.modules:
        logger_stub = types.SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda *a, **k: None,
        )
        sys.modules["loguru"] = types.SimpleNamespace(logger=logger_stub)

    if "httpx" not in sys.modules:
        sys.modules["httpx"] = types.SimpleNamespace(  # type: ignore[assignment]
            AsyncClient=object,
            HTTPStatusError=Exception,
            RequestError=Exception,
        )

    if "feedparser" not in sys.modules:
        sys.modules["feedparser"] = types.SimpleNamespace(parse=lambda *_a, **_k: {})

    class _BaseProviderStub:
        def __init__(self):
            self.runtime_proxy_url = None
            self.runtime_api_key = None
            self.runtime_contact_email = None

    sys.modules["athena.adapters.base"] = types.SimpleNamespace(BaseSearchProvider=_BaseProviderStub)
    sys.modules["athena.core.config"] = types.SimpleNamespace(
        Settings=object,
        get_settings=lambda: types.SimpleNamespace(
            outbound_proxy=None,
            openalex_email="test@example.com",
        )
    )

    module_path = Path(__file__).resolve().parents[1] / "athena" / "adapters" / "arxiv.py"
    spec = importlib.util.spec_from_file_location("arxiv_runtime_test_module", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, original in originals.items():
        if original is None:
            sys.modules.pop(key, None)
        else:
            sys.modules[key] = original
    return module


def test_retry_for_low_count_multi_term_query_on_first_attempt() -> None:
    module = _load_arxiv_module()
    provider = module.ArxivProvider()
    assert provider._should_retry_low_count(
        query="federated learning, sepsis",
        result_count=83,
        attempt=1,
    )


def test_no_retry_for_single_term_query() -> None:
    module = _load_arxiv_module()
    provider = module.ArxivProvider()
    assert not provider._should_retry_low_count(
        query="sepsis",
        result_count=83,
        attempt=1,
    )


def test_no_retry_on_last_attempt() -> None:
    module = _load_arxiv_module()
    provider = module.ArxivProvider()
    assert not provider._should_retry_low_count(
        query="federated learning, sepsis",
        result_count=83,
        attempt=provider.RETRY_ATTEMPTS,
    )
