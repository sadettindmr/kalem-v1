import re
import unicodedata

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from athena.models.author import Author
from athena.models.library import DownloadStatus, LibraryEntry, SourceType
from athena.models.paper import Paper
from athena.models.tag import Tag
from athena.schemas.search import PaperResponse, PaperSource


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
        PaperSource.MANUAL: SourceType.MANUAL,
    }
    return mapping.get(paper_source, SourceType.MANUAL)


class LibraryService:
    """Kütüphane yönetim servisi - arama sonuçlarını veritabanına kaydeder."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
