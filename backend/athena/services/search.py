import asyncio
import re
import unicodedata

from loguru import logger

from athena.adapters import ArxivProvider, CoreProvider, CrossrefProvider, OpenAlexProvider, SemanticScholarProvider
from athena.adapters.base import BaseSearchProvider
from athena.schemas.search import PaperResponse, PaperSource, SearchFilters, SearchMeta, SearchResponse


class SearchService:
    """Arama servis katmani - adaptorleri paralel calistirir ve sonuclari birlestirir."""

    def __init__(self) -> None:
        self.providers: list[BaseSearchProvider] = [
            SemanticScholarProvider(),
            OpenAlexProvider(),
            ArxivProvider(),
            CrossrefProvider(),
            CoreProvider(),
        ]

    async def search_papers(self, filters: SearchFilters) -> SearchResponse:
        """Tum adaptorlerden paralel arama yapar ve sonuclari birlestirir.

        Args:
            filters: Arama kriterleri

        Returns:
            SearchResponse: Tekillestirilmis makale listesi + meta istatistikler
        """
        # Sorguyu normalize et: virgulleri bosluklara cevir
        normalized_query = re.sub(r"\s*,\s*", " ", filters.query).strip()
        normalized_query = re.sub(r"\s+", " ", normalized_query)
        normalized_filters = filters.model_copy(update={"query": normalized_query})

        # Paralel arama
        tasks = [provider.search(normalized_filters) for provider in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Provider adlarini mapping ile tanimla
        provider_raw_keys = {
            "SemanticScholarProvider": ("raw_semantic", "Semantic Scholar"),
            "OpenAlexProvider": ("raw_openalex", "OpenAlex"),
            "ArxivProvider": ("raw_arxiv", "arXiv"),
            "CrossrefProvider": ("raw_crossref", "Crossref"),
            "CoreProvider": ("raw_core", "CORE"),
        }

        # Flatten: Tum sonuclari tek listede birlestir + kaynak bazli sayimlar
        raw_counts: dict[str, int] = {}
        errors: list[str] = []
        all_papers: list[PaperResponse] = []
        for i, result in enumerate(results):
            provider_class = type(self.providers[i]).__name__
            raw_key, display_name = provider_raw_keys.get(provider_class, (None, provider_class))

            if isinstance(result, Exception):
                error_msg = f"{display_name}: {type(result).__name__} - {result}"
                errors.append(error_msg)
                logger.error(f"Provider error: {error_msg}")
                if raw_key:
                    raw_counts[raw_key] = 0
                continue

            if raw_key:
                raw_counts[raw_key] = len(result)
            all_papers.extend(result)

        # Keyword relevance filtresi
        # Virgullerle ayrilmis konsept gruplarini olustur
        # "federated learning, sepsis" → [["federated", "learning"], ["sepsis"]]
        # Her gruptan en az bir kelime baslik/ozette gecmeli
        raw_terms = [t.strip() for t in filters.query.lower().split(",") if t.strip()]
        keyword_groups = [t.split() for t in raw_terms] if raw_terms else [normalized_query.lower().split()]
        filtered_papers = self._filter_by_relevance(all_papers, keyword_groups)
        relevance_removed = len(all_papers) - len(filtered_papers)
        if relevance_removed > 0:
            logger.info(f"Relevance filter: {relevance_removed} irrelevant papers removed")

        # Deduplication
        unique_papers = self._deduplicate(filtered_papers)
        raw_total = sum(raw_counts.values())
        duplicates_removed = raw_total - relevance_removed - len(unique_papers)

        meta = SearchMeta(
            **raw_counts,
            duplicates_removed=duplicates_removed,
            total=len(unique_papers),
            errors=errors,
        )

        return SearchResponse(results=unique_papers, meta=meta)

    # Kaynak oncelik sirasi: dusuk sayi = yuksek oncelik
    SOURCE_PRIORITY: dict[PaperSource, int] = {
        PaperSource.SEMANTIC: 1,   # En zengin metadata
        PaperSource.CROSSREF: 2,   # En dogru DOI
        PaperSource.ARXIV: 3,      # En guncel pre-print
        PaperSource.OPENALEX: 4,
        PaperSource.CORE: 5,
        PaperSource.MANUAL: 6,
    }

    @staticmethod
    def _normalize_title(title: str) -> str:
        """Baslik normalizasyonu - deduplication icin agresif temizleme.

        - Unicode normalizasyonu (aksanli karakterleri ASCII'ye cevir)
        - Tum noktalama isaretlerini kaldir
        - Fazladan bosluklari temizle
        - Stop word'leri kaldir (the, a, an, of, in, on, for, and, or, to, with)
        - Sadece alfanumerik karakterler kalir
        - Ornek: "Deep Learning: A Review" == "deep learning review"
                 "The Impact of AI on Healthcare" == "impact ai healthcare"
        """
        # Lowercase
        text = title.lower().strip()

        # Unicode normalizasyonu: aksanli karakterleri ASCII'ye cevir
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

        # Noktalama isaretlerini kaldir (sadece alfanumerik ve bosluk kalsin)
        text = re.sub(r"[^a-z0-9\s]", "", text)

        # Stop word'leri kaldir
        stop_words = {"the", "a", "an", "of", "in", "on", "for", "and", "or", "to", "with"}
        words = text.split()
        words = [w for w in words if w not in stop_words]

        # Fazladan bosluklari temizle
        return " ".join(words)

    def _deduplicate(self, papers: list[PaperResponse]) -> list[PaperResponse]:
        """Sonuclari 2 adimli deduplication ile tekillestirir.

        Adim 1: DOI eslesmesi (kesin)
        Adim 2: Normalized title eslesmesi (DOI yoksa)

        Oncelik sirasi (cakismalarda ustteki korunur):
        1. Semantic Scholar (En zengin metadata)
        2. Crossref (En dogru DOI)
        3. arXiv (En guncel pre-print)
        4. OpenAlex
        5. CORE
        """
        seen_dois: dict[str, int] = {}           # doi -> unique_papers index
        seen_titles: dict[str, int] = {}          # normalized_title -> unique_papers index
        unique_papers: list[PaperResponse] = []

        for paper in papers:
            doi_key = None
            if paper.external_id and paper.external_id.startswith("10."):
                doi_key = paper.external_id.lower().strip()

            norm_title = self._normalize_title(paper.title)

            # Adim 1: DOI eslesmesi
            if doi_key and doi_key in seen_dois:
                idx = seen_dois[doi_key]
                existing = unique_papers[idx]
                if self._has_higher_priority(paper, existing):
                    unique_papers[idx] = paper
                    seen_dois[doi_key] = idx
                    # Title index'ini de guncelle
                    old_norm = self._normalize_title(existing.title)
                    if old_norm in seen_titles:
                        del seen_titles[old_norm]
                    seen_titles[norm_title] = idx
                continue

            # Adim 2: Normalized title eslesmesi
            if norm_title and norm_title in seen_titles:
                idx = seen_titles[norm_title]
                existing = unique_papers[idx]
                if self._has_higher_priority(paper, existing):
                    unique_papers[idx] = paper
                    seen_titles[norm_title] = idx
                    # DOI index'ini guncelle
                    if doi_key:
                        seen_dois[doi_key] = idx
                continue

            # Yeni paper ekle
            idx = len(unique_papers)
            unique_papers.append(paper)
            if doi_key:
                seen_dois[doi_key] = idx
            if norm_title:
                seen_titles[norm_title] = idx

        return unique_papers

    def _has_higher_priority(self, new: PaperResponse, existing: PaperResponse) -> bool:
        """Yeni paper'in mevcut paper'dan daha yuksek oncelikli olup olmadigini kontrol eder."""
        new_priority = self.SOURCE_PRIORITY.get(new.source, 99)
        existing_priority = self.SOURCE_PRIORITY.get(existing.source, 99)
        return new_priority < existing_priority

    @staticmethod
    def _filter_by_relevance(papers: list[PaperResponse], keyword_groups: list[list[str]]) -> list[PaperResponse]:
        """Arama kelimeleriyle alakasiz sonuclari filtreler.

        Virgullerle ayrilmis her konsept grubundan en az bir kelime
        baslik veya ozette gecmeli. Bu sayede "federated learning, sepsis"
        aramasinda sadece her iki konuyu da iceren makaleler doner.

        Args:
            papers: Filtrelenecek makale listesi
            keyword_groups: Konsept gruplari - her gruptan en az bir kelime gecmeli
                Ornek: [["federated", "learning"], ["sepsis"]]

        Returns:
            Alakali makalelerin listesi
        """
        if not keyword_groups:
            return papers

        relevant: list[PaperResponse] = []
        for paper in papers:
            title_lower = paper.title.lower()
            abstract_lower = (paper.abstract or "").lower()
            searchable = f"{title_lower} {abstract_lower}"

            # Her konsept grubundan en az bir kelime gecmeli (AND mantigi)
            if all(
                any(kw in searchable for kw in group)
                for group in keyword_groups
            ):
                relevant.append(paper)

        return relevant
