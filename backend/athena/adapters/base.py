from abc import ABC, abstractmethod

from athena.schemas.search import PaperResponse, SearchFilters


class BaseSearchProvider(ABC):
    """Arama motorları için soyut temel sınıf (Interface).

    Tüm arama sağlayıcıları (Semantic Scholar, OpenAlex, vb.)
    bu sınıftan türetilmeli ve search metodunu implement etmelidir.
    """

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
