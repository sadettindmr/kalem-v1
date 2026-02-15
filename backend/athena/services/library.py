import re
import unicodedata

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from athena.models.author import Author
from athena.models.library import DownloadStatus, LibraryEntry, SourceType
from athena.models.paper import Paper
from athena.models.tag import Tag
from athena.schemas.search import PaperResponse, PaperSource, SearchFilters
from athena.services.search import SearchService


def slugify(text: str) -> str:
    """Metni URL-friendly slug formatına dönüştürür.

    Args:
        text: Dönüştürülecek metin

    Returns:
        Slug formatında metin
    """
    # Unicode karakterleri ASCII'ye dönüştür
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Küçük harfe çevir
    text = text.lower()
    # Alfanumerik olmayan karakterleri tire ile değiştir
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Baştaki ve sondaki tireleri kaldır
    text = text.strip("-")
    # Maksimum 255 karakter
    return text[:255]


def map_source(paper_source: PaperSource) -> SourceType:
    """PaperSource (schema) -> SourceType (model) dönüşümü."""
    mapping = {
        PaperSource.SEMANTIC: SourceType.SEMANTIC,
        PaperSource.OPENALEX: SourceType.OPENALEX,
        PaperSource.ARXIV: SourceType.ARXIV,
        PaperSource.CROSSREF: SourceType.CROSSREF,
        PaperSource.CORE: SourceType.CORE,
        PaperSource.MANUAL: SourceType.MANUAL,
    }
    return mapping.get(paper_source, SourceType.MANUAL)


class LibraryService:
    """Kütüphane yönetim servisi - arama sonuçlarını veritabanına kaydeder."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_service = SearchService(db)

    async def get_library_entries(
        self,
        page: int = 1,
        limit: int = 20,
        tag: str | None = None,
        status: str | None = None,
        min_citations: int | None = None,
        year_start: int | None = None,
        year_end: int | None = None,
        search: str | None = None,
    ) -> tuple[list[LibraryEntry], int]:
        """Kutuphane kayitlarini filtreleyerek getirir.

        Search doluysa PostgreSQL Full-Text Search + fallback ilike uygular.
        """
        query = select(LibraryEntry).options(
            joinedload(LibraryEntry.paper),
            joinedload(LibraryEntry.tags),
        )
        query = query.join(LibraryEntry.paper)

        if status:
            try:
                query = query.where(
                    LibraryEntry.download_status == DownloadStatus(status.lower())
                )
            except ValueError:
                pass

        if tag:
            query = query.join(LibraryEntry.tags).where(Tag.name == tag.lower())

        if min_citations is not None:
            query = query.where(Paper.citation_count >= min_citations)

        if year_start is not None:
            query = query.where(Paper.year >= year_start)
        if year_end is not None:
            query = query.where(Paper.year <= year_end)

        rank_expr = None
        if search:
            search_term = f"%{search.lower()}%"
            ts_query = func.websearch_to_tsquery("english", search)
            fts_match = Paper.search_vector.op("@@")(ts_query)

            author_subquery = (
                select(LibraryEntry.id)
                .join(LibraryEntry.paper)
                .join(Paper.authors)
                .where(func.lower(Author.name).like(search_term))
            )
            tag_subquery = (
                select(LibraryEntry.id)
                .join(LibraryEntry.tags)
                .where(func.lower(Tag.name).like(search_term))
            )

            fallback_match = (
                func.lower(Paper.title).like(search_term)
                | func.lower(func.coalesce(Paper.abstract, "")).like(search_term)
                | LibraryEntry.id.in_(author_subquery)
                | LibraryEntry.id.in_(tag_subquery)
            )

            query = query.where(fts_match | fallback_match)
            rank_expr = func.ts_rank(Paper.search_vector, ts_query)

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        if rank_expr is not None:
            query = query.order_by(rank_expr.desc(), LibraryEntry.id.desc())
        else:
            query = query.order_by(LibraryEntry.id.desc())

        result = await self.db.execute(query)
        entries = result.unique().scalars().all()
        return list(entries), total

    async def enrich_missing_metadata(self, limit: int = 20) -> dict:
        """Kutuphanedeki eksik metadata'lari dis kaynaklardan tamamlar.

        Is kurali:
        - Sadece eksik metadata'ya sahip paper'lar islenir.
        - DOI varsa DOI ile, yoksa baslik ile arama yapilir.
        - Eslesmelerde once DOI, sonra normalize baslik kullanilir.
        - Sadece eksik alanlar guncellenir.
        """
        stmt = (
            select(LibraryEntry)
            .options(
                selectinload(LibraryEntry.paper).selectinload(Paper.authors),
            )
            .join(LibraryEntry.paper)
            .order_by(LibraryEntry.id.desc())
        )
        result = await self.db.execute(stmt)
        entries = result.scalars().all()

        processed = 0
        updated = 0
        skipped = 0
        failed = 0
        details: list[dict] = []

        for entry in entries:
            if processed >= limit:
                break

            paper = entry.paper
            if paper is None:
                skipped += 1
                continue

            if not self._needs_metadata_enrichment(paper):
                skipped += 1
                continue

            processed += 1
            query = paper.doi if paper.doi else paper.title

            try:
                search_response = await self.search_service.search_papers(
                    SearchFilters(query=query)
                )
                match = self._find_best_match(paper, search_response.results)
                if not match:
                    skipped += 1
                    details.append(
                        {
                            "entry_id": entry.id,
                            "paper_id": paper.id,
                            "status": "no_match",
                        }
                    )
                    continue

                changed = await self._apply_metadata_update(paper, match)
                if changed:
                    updated += 1
                    details.append(
                        {
                            "entry_id": entry.id,
                            "paper_id": paper.id,
                            "status": "updated",
                        }
                    )
                else:
                    skipped += 1
                    details.append(
                        {
                            "entry_id": entry.id,
                            "paper_id": paper.id,
                            "status": "no_change",
                        }
                    )
            except Exception as exc:
                failed += 1
                details.append(
                    {
                        "entry_id": entry.id,
                        "paper_id": paper.id,
                        "status": "failed",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        await self.db.commit()

        return {
            "processed": processed,
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "details": details,
        }

    async def get_saved_external_ids(self, external_ids: list[str]) -> set[str]:
        """Verilen external_id'lerden kutuphanede kayitli olanlari dondurur."""
        if not external_ids:
            return set()

        # DOI'ler (10. ile baslayanlar) ve diger ID'ler
        dois = [eid for eid in external_ids if eid.startswith("10.")]
        other_ids = [eid for eid in external_ids if not eid.startswith("10.")]

        saved: set[str] = set()

        # DOI ile kontrol
        if dois:
            stmt = (
                select(Paper.doi)
                .join(LibraryEntry, LibraryEntry.paper_id == Paper.id)
                .where(Paper.doi.in_(dois))
            )
            result = await self.db.execute(stmt)
            saved.update(row[0] for row in result.all() if row[0])

        # Diger external_id'ler icin title_slug ile kontrol
        # (Semantic Scholar paperId gibi DOI olmayan ID'ler)
        if other_ids:
            # Bu ID'ler genelde paperId, bunlari title_slug'a cevirip kontrol edemeyiz
            # Ama paper tablosunda DOI olmadan kaydedilmis olabilirler
            # Simdilik sadece DOI bazli kontrol yeterli
            pass

        return saved

    async def is_paper_in_library(self, paper_data: PaperResponse) -> bool:
        """Makalenin kutuphanede kayitli olup olmadigini kontrol eder."""
        title_slug = slugify(paper_data.title)

        # DOI ile kontrol
        if paper_data.external_id and paper_data.external_id.startswith("10."):
            stmt = (
                select(LibraryEntry.id)
                .join(Paper, LibraryEntry.paper_id == Paper.id)
                .where(Paper.doi == paper_data.external_id)
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                return True

        # title_slug ile kontrol
        stmt = (
            select(LibraryEntry.id)
            .join(Paper, LibraryEntry.paper_id == Paper.id)
            .where(Paper.title_slug == title_slug)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def add_paper_to_library(
        self, paper_data: PaperResponse, search_query: str
    ) -> LibraryEntry:
        """Makaleyi kütüphaneye ekler.

        Args:
            paper_data: Arama sonucundan gelen makale verisi
            search_query: Kullanıcının arama terimi (etiketleme için)

        Returns:
            Oluşturulan LibraryEntry objesi (ID dahil)
        """
        # 1. Deduplication: Mevcut makaleyi kontrol et
        paper = await self._find_or_create_paper(paper_data)

        # 2. LibraryEntry oluştur veya mevcut olanı al
        library_entry = await self._find_or_create_library_entry(paper, paper_data)

        # 3. Auto-tagging
        await self._process_tags(library_entry, search_query)

        # Değişiklikleri kaydet
        await self.db.commit()
        await self.db.refresh(library_entry)

        return library_entry

    async def _find_or_create_paper(self, paper_data: PaperResponse) -> Paper:
        """Makaleyi veritabanında bulur veya yeni oluşturur.

        Deduplication önceliği:
        1. DOI ile kontrol (varsa)
        2. title_slug ile kontrol
        """
        title_slug = slugify(paper_data.title)

        # DOI ile kontrol
        if paper_data.external_id and paper_data.external_id.startswith("10."):
            stmt = select(Paper).where(Paper.doi == paper_data.external_id)
            result = await self.db.execute(stmt)
            existing_paper = result.scalar_one_or_none()
            if existing_paper:
                return existing_paper

        # title_slug ile kontrol
        stmt = select(Paper).where(Paper.title_slug == title_slug)
        result = await self.db.execute(stmt)
        existing_paper = result.scalar_one_or_none()
        if existing_paper:
            return existing_paper

        # Yeni Paper oluştur
        paper = Paper(
            doi=paper_data.external_id if paper_data.external_id and paper_data.external_id.startswith("10.") else None,
            title=paper_data.title,
            title_slug=title_slug,
            abstract=paper_data.abstract,
            year=paper_data.year,
            citation_count=paper_data.citation_count,
            venue=paper_data.venue,
            pdf_url=paper_data.pdf_url,
        )
        self.db.add(paper)
        await self.db.flush()  # ID almak için

        # Yazarları ekle
        await self._add_authors(paper, paper_data)

        return paper

    async def _add_authors(self, paper: Paper, paper_data: PaperResponse) -> None:
        """Yazarları veritabanına ekler ve makaleyle ilişkilendirir.

        Not: Bu metod sadece yeni oluşturulan paper'lar için çağrılır.
        Async lazy loading sorununu önlemek için önce refresh yapıyoruz.
        """
        # Async lazy loading için önce relationship'i yükle
        await self.db.refresh(paper, ["authors"])

        for author_data in paper_data.authors:
            author_slug = slugify(author_data.name)

            # Mevcut yazarı bul veya oluştur
            stmt = select(Author).where(Author.slug == author_slug)
            result = await self.db.execute(stmt)
            author = result.scalar_one_or_none()

            if not author:
                author = Author(name=author_data.name, slug=author_slug)
                self.db.add(author)
                await self.db.flush()

            # Paper-Author ilişkisi
            paper.authors.append(author)

    async def _find_or_create_library_entry(
        self, paper: Paper, paper_data: PaperResponse
    ) -> LibraryEntry:
        """LibraryEntry bulur veya oluşturur."""
        # Mevcut entry kontrol
        stmt = select(LibraryEntry).where(LibraryEntry.paper_id == paper.id)
        result = await self.db.execute(stmt)
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            return existing_entry

        # Yeni LibraryEntry oluştur
        library_entry = LibraryEntry(
            paper_id=paper.id,
            source=map_source(paper_data.source),
            download_status=DownloadStatus.PENDING,
        )
        self.db.add(library_entry)
        await self.db.flush()

        return library_entry

    async def _process_tags(
        self, library_entry: LibraryEntry, search_query: str
    ) -> None:
        """Arama terimlerinden etiketler oluşturur ve ilişkilendirir.

        Not: Bu metod yeni veya mevcut library_entry için çağrılabilir.
        Mevcut entry için tags'ı async olarak yüklemeliyiz.
        """
        # Virgülle ayır ve temizle
        tag_names = [tag.strip().lower() for tag in search_query.split(",") if tag.strip()]

        if not tag_names:
            return

        # Mevcut tag'leri async olarak yükle
        await self.db.refresh(library_entry, ["tags"])
        existing_tag_names = {tag.name for tag in library_entry.tags}

        for tag_name in tag_names:
            # Maksimum 100 karakter
            tag_name = tag_name[:100]

            # Zaten varsa atla
            if tag_name in existing_tag_names:
                continue

            # Mevcut etiketi bul veya oluştur
            stmt = select(Tag).where(Tag.name == tag_name)
            result = await self.db.execute(stmt)
            tag = result.scalar_one_or_none()

            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
                await self.db.flush()

            # LibraryEntry-Tag ilişkisi
            library_entry.tags.append(tag)
            existing_tag_names.add(tag_name)

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        """Basliklari karsilastirma icin normalize eder."""
        normalized = unicodedata.normalize("NFKD", text)
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = normalized.lower().strip()
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    @staticmethod
    def _needs_metadata_enrichment(paper: Paper) -> bool:
        """Paper'da eksik metadata olup olmadigini kontrol eder."""
        has_no_authors = len(paper.authors) == 0
        return any(
            [
                not paper.abstract,
                not paper.year,
                not paper.venue,
                (paper.citation_count or 0) == 0,
                not paper.pdf_url,
                has_no_authors,
            ]
        )

    def _find_best_match(
        self, paper: Paper, candidates: list[PaperResponse]
    ) -> PaperResponse | None:
        """Arama sonucundan en uygun kaydi secer."""
        if not candidates:
            return None

        if paper.doi:
            paper_doi = paper.doi.lower().strip()
            for item in candidates:
                if item.external_id and item.external_id.lower().strip() == paper_doi:
                    return item

        normalized_title = self._normalize_for_match(paper.title)
        for item in candidates:
            if self._normalize_for_match(item.title) == normalized_title:
                return item

        return candidates[0]

    async def _apply_metadata_update(self, paper: Paper, match: PaperResponse) -> bool:
        """Eslesen kayittan sadece eksik alanlari gunceller."""
        changed = False

        if not paper.abstract and match.abstract:
            paper.abstract = match.abstract
            changed = True

        if not paper.year and match.year:
            paper.year = match.year
            changed = True

        if not paper.venue and match.venue:
            paper.venue = match.venue
            changed = True

        if (paper.citation_count or 0) == 0 and (match.citation_count or 0) > 0:
            paper.citation_count = match.citation_count
            changed = True

        if not paper.pdf_url and match.pdf_url:
            paper.pdf_url = match.pdf_url
            changed = True

        # DOI yoksa ve eslesen kayit DOI ise doldur
        if (
            not paper.doi
            and match.external_id
            and match.external_id.startswith("10.")
        ):
            paper.doi = match.external_id
            changed = True

        # Author'lari sadece bossa tamamla
        await self.db.refresh(paper, ["authors"])
        if len(paper.authors) == 0 and match.authors:
            for author_data in match.authors:
                author_slug = slugify(author_data.name)
                stmt = select(Author).where(Author.slug == author_slug)
                result = await self.db.execute(stmt)
                author = result.scalar_one_or_none()
                if not author:
                    author = Author(name=author_data.name, slug=author_slug)
                    self.db.add(author)
                    await self.db.flush()
                paper.authors.append(author)
            changed = True

        return changed
