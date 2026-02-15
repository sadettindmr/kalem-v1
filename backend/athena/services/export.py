"""Kütüphane dışa aktarma servisi.

Sprint 4.3 - Library Export Service
- CSV ve XLSX formatlarında dışa aktarma
- Pandas DataFrame kullanımı
- StreamingResponse ile dosya indirme
"""

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
        """LibraryEntry listesinden Pandas DataFrame oluşturur.

        TDD Bölüm 3.5'e göre sütunlar:
        - ID, Title, Authors, Year, Venue, DOI, Citation Count, Source, Tags
        """
        data = []

        for entry in entries:
            paper = entry.paper

            # Authors: virgülle ayrılmış
            authors = ", ".join(a.name for a in paper.authors)

            # Tags: virgülle ayrılmış
            tags = ", ".join(t.name for t in entry.tags)

            row = {
                "ID": entry.id,
                "Title": paper.title,
                "Authors": authors,
                "Year": paper.year,
                "Venue": paper.venue or "",
                "DOI": paper.doi or "",
                "Citation Count": paper.citation_count,
                "Source": entry.source.value,
                "Tags": tags,
            }
            data.append(row)

        return pd.DataFrame(data)

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
            "athena_library_export.csv",
        )

    def _export_xlsx(self, df: pd.DataFrame) -> tuple[BytesIO, str, str]:
        """DataFrame'i XLSX formatında dışa aktarır.

        Returns:
            Tuple: (BytesIO buffer, content_type, filename)
        """
        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Library")

        buffer.seek(0)

        return (
            buffer,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "athena_library_export.xlsx",
        )
