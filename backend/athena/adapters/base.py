from abc import ABC, abstractmethod

from athena.schemas.search import PaperResponse, SearchFilters


class BaseSearchProvider(ABC):
    """Arama motorları için soyut temel sınıf (Interface).

    Tüm arama sağlayıcıları (Semantic Scholar, OpenAlex, vb.)
    bu sınıftan türetilmeli ve search metodunu implement etmelidir.
    """
    provider_id: str = "base"

    def __init__(self) -> None:
        self.runtime_proxy_url: str | None = None
        self.runtime_api_key: str | None = None
        self.runtime_contact_email: str | None = None

    def configure_runtime(
        self,
        *,
        proxy_url: str | None = None,
        api_key: str | None = None,
        contact_email: str | None = None,
    ) -> None:
        """Request scope ayarlarini provider instance'ina uygular."""
        self.runtime_proxy_url = proxy_url
        self.runtime_api_key = api_key
        self.runtime_contact_email = contact_email

    @abstractmethod
    async def search(self, filters: SearchFilters) -> list[PaperResponse]:
        """Verilen filtrelere göre makale araması yapar.

        Args:
            filters: Arama kriterleri (query, year_start, year_end, min_citations)

        Returns:
            Bulunan makalelerin listesi

        Raises:
            NotImplementedError: Alt sınıf implement etmezse
        """
        pass
