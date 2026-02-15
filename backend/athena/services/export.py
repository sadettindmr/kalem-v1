"""Kütüphane dışa aktarma servisi.

Sprint 12.1 - Gelismis Bibliyografik Export:
- Akademik odakli kolon yapisi (APA/IEEE dahil)
- CSV ve XLSX formatlarında dışa aktarma
- XLSX auto-width
"""

from datetime import datetime
from io import BytesIO
from typing import Literal

import pandas as pd
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from athena.models.library import LibraryEntry
from athena.models.tag import Tag


class ExportService:
    """Kütüphane verilerini dışa aktaran servis."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_library(
        self,
        format: Literal["csv", "xlsx"] = "xlsx",
        search_query: str | None = None,
    ) -> tuple[BytesIO, str, str]:
        """Kütüphane verilerini belirtilen formatta dışa aktarır.

        Args:
            format: Çıktı formatı ("csv" veya "xlsx")
            search_query: Opsiyonel etiket filtresi

        Returns:
            Tuple: (dosya içeriği, content_type, dosya adı)
        """
        # 1. Veritabanından verileri çek
        entries = await self._fetch_library_entries(search_query)

        # 2. DataFrame oluştur
        df = self._create_dataframe(entries)

        logger.info(f"Exporting {len(df)} entries in {format} format")

        # 3. Dosyayı oluştur
        if format == "csv":
            return self._export_csv(df)
        else:
            return self._export_xlsx(df)

    async def _fetch_library_entries(
        self, search_query: str | None = None
    ) -> list[LibraryEntry]:
        """Filtrelenmiş kütüphane girişlerini veritabanından çeker.

        Args:
            search_query: Opsiyonel etiket filtresi

        Returns:
            LibraryEntry listesi
        """
        query = select(LibraryEntry).options(
            joinedload(LibraryEntry.paper),
            joinedload(LibraryEntry.tags),
        )

        # Tag filtresi (search_query varsa)
        if search_query:
            # Virgülle ayrılmış tag'leri al
            tag_names = [t.strip().lower() for t in search_query.split(",") if t.strip()]
            if tag_names:
                query = query.join(LibraryEntry.tags).where(Tag.name.in_(tag_names))

        query = query.order_by(LibraryEntry.id.desc())

        result = await self.db.execute(query)
        entries = result.unique().scalars().all()

        # Authors'ı yükle (async lazy loading için)
        for entry in entries:
            await self.db.refresh(entry.paper, ["authors"])

        return list(entries)

    def _create_dataframe(self, entries: list[LibraryEntry]) -> pd.DataFrame:
        """LibraryEntry listesinden Sprint 12.1 kolon yapisinda DataFrame olusturur."""
        data = []
        citation_col = f"Citation as of {datetime.now().strftime('%d.%m.%Y')}"

        for entry in entries:
            paper = entry.paper

            authors = ", ".join(a.name for a in paper.authors)
            search_words = ", ".join(t.name for t in entry.tags)
            doi_or_link = self._doi_or_link(paper.doi, paper.pdf_url)

            row = {
                "Makale Adı": paper.title,
                "Yazar(lar)": authors,
                "Yayın Yılı": paper.year,
                "Makale Türü": self._article_type(paper.venue),
                "Yayın Platformu / Dergi": paper.venue or "",
                "DOI / Link": doi_or_link,
                "Keywords": "",
                "Search Words": search_words,
                "Citation (APA)": self.format_apa(paper.title, paper.authors, paper.year, paper.venue),
                "Citation (IEEE)": self.format_ieee(paper.title, paper.authors, paper.year, paper.venue),
                citation_col: paper.citation_count,
                "Source": entry.source.value.title(),
                "Downloaded": "EVET" if entry.download_status.value == "completed" else "HAYIR",
                "Kod/Veri Erişilebilirliği": self._code_data_availability(
                    paper.pdf_url,
                    paper.abstract,
                ),
            }
            data.append(row)

        return pd.DataFrame(data)

    @staticmethod
    def _article_type(venue: str | None) -> str:
        venue_text = (venue or "").lower()
        if "journal" in venue_text:
            return "Dergi Makalesi"
        if "conf" in venue_text:
            return "Bildiri"
        return "Diğer"

    @staticmethod
    def _doi_or_link(doi: str | None, pdf_url: str | None) -> str:
        if doi:
            return f"https://doi.org/{doi}"
        if pdf_url:
            return pdf_url
        return ""

    @staticmethod
    def _initials(name_parts: list[str]) -> str:
        return " ".join(f"{part[0]}." for part in name_parts if part)

    def _format_author_apa(self, author_name: str) -> str:
        parts = [p for p in author_name.strip().split() if p]
        if not parts:
            return "Unknown"
        if len(parts) == 1:
            return parts[0]
        last_name = parts[-1]
        initials = self._initials(parts[:-1])
        return f"{last_name}, {initials}".strip()

    def _format_author_ieee(self, author_name: str) -> str:
        parts = [p for p in author_name.strip().split() if p]
        if not parts:
            return "Unknown"
        if len(parts) == 1:
            return parts[0]
        last_name = parts[-1]
        initials = self._initials(parts[:-1])
        return f"{initials} {last_name}".strip()

    def format_apa(
        self,
        title: str,
        authors: list,
        year: int | None,
        venue: str | None,
    ) -> str:
        """Best-effort APA atif metni olusturur."""
        author_names = [self._format_author_apa(a.name) for a in authors] if authors else ["Unknown"]
        author_text = ", ".join(author_names)
        year_text = str(year) if year else "n.d."
        venue_text = venue or "Unknown Venue"
        return f"{author_text} ({year_text}). {title}. {venue_text}."

    def format_ieee(
        self,
        title: str,
        authors: list,
        year: int | None,
        venue: str | None,
    ) -> str:
        """Best-effort IEEE atif metni olusturur."""
        author_names = [self._format_author_ieee(a.name) for a in authors] if authors else ["Unknown"]
        author_text = ", ".join(author_names)
        venue_text = venue or "Unknown Venue"
        year_text = str(year) if year else "n.d."
        return f"{author_text}, '{title},' in {venue_text}, {year_text}."

    @staticmethod
    def _code_data_availability(pdf_url: str | None, abstract: str | None) -> str:
        text = f"{pdf_url or ''} {abstract or ''}".lower()
        markers = ("github.com", "gitlab.com", "zenodo")
        return "Muhtemelen Var" if any(marker in text for marker in markers) else "Belirtilmemiş"

    def _export_csv(self, df: pd.DataFrame) -> tuple[BytesIO, str, str]:
        """DataFrame'i CSV formatında dışa aktarır.

        Returns:
            Tuple: (BytesIO buffer, content_type, filename)
        """
        buffer = BytesIO()
        df.to_csv(buffer, index=False, encoding="utf-8")
        buffer.seek(0)

        return (
            buffer,
            "text/csv; charset=utf-8",
            "kalem_kasghar_library_export.csv",
        )

    def _export_xlsx(self, df: pd.DataFrame) -> tuple[BytesIO, str, str]:
        """DataFrame'i XLSX formatında dışa aktarır.

        Returns:
            Tuple: (BytesIO buffer, content_type, filename)
        """
        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Library")
            worksheet = writer.sheets["Library"]

            # Kolon genisliklerini icerige gore ayarla (auto-width)
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    value = "" if cell.value is None else str(cell.value)
                    if len(value) > max_length:
                        max_length = len(value)
                worksheet.column_dimensions[column_letter].width = min(max_length + 2, 80)

        buffer.seek(0)

        return (
            buffer,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "kalem_kasghar_library_export.xlsx",
        )
