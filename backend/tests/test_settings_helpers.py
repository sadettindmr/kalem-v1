import importlib.util
from pathlib import Path


def _load_module(module_name: str, relative_path: str):
    module_path = Path(__file__).resolve().parents[1] / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mask_secret_sk_prefix():
    router_module = _load_module(
        "settings_router_for_test", "athena/api/v2/routers/settings.py"
    )
    assert router_module._mask_secret("sk-live-123456") == "sk-***"


def test_mask_secret_empty():
    router_module = _load_module(
        "settings_router_for_test_empty", "athena/api/v2/routers/settings.py"
    )
    assert router_module._mask_secret("") is None
    assert router_module._mask_secret(None) is None


def test_normalize_providers_filters_invalid_and_duplicates():
    service_module = _load_module(
        "settings_service_for_test", "athena/services/settings.py"
    )
    service = service_module.UserSettingsService(db=None)  # type: ignore[arg-type]
    normalized = service._normalize_providers(
        ["Semantic", "semantic", "openalex", "invalid-provider", " "]
    )
    assert normalized == ["semantic", "openalex"]

