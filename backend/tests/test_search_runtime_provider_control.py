import asyncio
import importlib.util
import sys
import types
from pathlib import Path

from athena.schemas.search import PaperResponse, PaperSource
from athena.schemas.search import SearchFilters


def _load_search_module():
    # loguru olmayan lightweight ortamlarda import kirilmasin
    if "loguru" not in sys.modules:
        logger_stub = types.SimpleNamespace(
            info=lambda *a, **k: None,
            warning=lambda *a, **k: None,
            error=lambda *a, **k: None,
        )
        sys.modules["loguru"] = types.SimpleNamespace(logger=logger_stub)

    # Adapter bagimliliklarini testte minimal tut
    adapters_base_stub = types.SimpleNamespace(BaseSearchProvider=object)

    class _ProviderStub:
        provider_id = "stub"

        def __init__(self):
            pass

    adapters_stub = types.SimpleNamespace(
        ArxivProvider=_ProviderStub,
        CoreProvider=_ProviderStub,
        CrossrefProvider=_ProviderStub,
        OpenAlexProvider=_ProviderStub,
        SemanticScholarProvider=_ProviderStub,
    )

    sys.modules["athena.adapters.base"] = adapters_base_stub
    sys.modules["athena.adapters"] = adapters_stub

    module_path = Path(__file__).resolve().parents[1] / "athena" / "services" / "search.py"
    spec = importlib.util.spec_from_file_location("search_runtime_test_module", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeProvider:
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.called = False
        self.runtime_proxy_url = None
        self.runtime_api_key = None
        self.runtime_contact_email = None

    def configure_runtime(self, *, proxy_url=None, api_key=None, contact_email=None):
        self.runtime_proxy_url = proxy_url
        self.runtime_api_key = api_key
        self.runtime_contact_email = contact_email

    async def search(self, filters):
        self.called = True
        return []


class _RogueCrossrefProvider(_FakeProvider):
    async def search(self, filters):
        self.called = True
        return [
            PaperResponse(
                title="Crossref Paper",
                abstract=None,
                year=2024,
                citation_count=10,
                venue="Test Venue",
                authors=[],
                source=PaperSource.CROSSREF,
                external_id="10.1234/test",
                pdf_url=None,
            )
        ]


def test_search_service_respects_enabled_providers_and_runtime_injection():
    module = _load_search_module()
    service = module.SearchService(db=None)

    semantic = _FakeProvider("semantic")
    core = _FakeProvider("core")
    openalex = _FakeProvider("openalex")
    service.providers = [semantic, core, openalex]

    async def _fake_runtime():
        return module.RuntimeSearchSettings(
            enabled_providers=["core"],
            semantic_scholar_api_key="semantic-key",
            core_api_key="core-key",
            contact_email="runtime@example.com",
            proxy_url="http://proxy.local:8080",
        )

    service._load_runtime_settings = _fake_runtime

    response = asyncio.run(service.search_papers(SearchFilters(query="deep learning")))

    assert semantic.called is False
    assert openalex.called is False
    assert core.called is True

    assert core.runtime_api_key == "core-key"
    assert core.runtime_contact_email == "runtime@example.com"
    assert core.runtime_proxy_url == "http://proxy.local:8080"

    assert response.meta.raw_semantic == 0
    assert response.meta.raw_openalex == 0
    assert response.meta.raw_core == 0


def test_search_service_filters_out_disabled_source_payloads():
    module = _load_search_module()
    service = module.SearchService(db=None)

    # provider_id semantic olsa bile crossref source donuyor (defensive filter testi)
    rogue = _RogueCrossrefProvider("semantic")
    service.providers = [rogue]

    async def _fake_runtime():
        return module.RuntimeSearchSettings(
            enabled_providers=["semantic"],
            semantic_scholar_api_key=None,
            core_api_key=None,
            contact_email="runtime@example.com",
            proxy_url=None,
        )

    service._load_runtime_settings = _fake_runtime
    response = asyncio.run(service.search_papers(SearchFilters(query="test query")))

    assert rogue.called is True
    assert response.meta.raw_crossref == 0
    assert response.meta.total == 0
    assert response.results == []
