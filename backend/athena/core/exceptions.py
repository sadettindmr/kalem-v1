"""Kalem - Kasghar özel hata sınıfları ve hata kodları.

TDD Bölüm 5 standartlarına uygun hata yönetimi.
"""

import enum
from typing import Optional


class ErrorCode(str, enum.Enum):
    """Standart hata kodları."""

    # Genel hatalar
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"

    # Provider (Arama) hataları
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_INVALID_RESPONSE = "PROVIDER_INVALID_RESPONSE"

    # Kütüphane hataları
    LIBRARY_DUPLICATE = "LIBRARY_DUPLICATE"
    LIBRARY_NOT_FOUND = "LIBRARY_NOT_FOUND"

    # İndirme hataları
    DOWNLOAD_NO_PDF_URL = "DOWNLOAD_NO_PDF_URL"
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"


class AthenaError(Exception):
    """Kalem - Kasghar uygulaması için temel hata sınıfı.

    Attributes:
        code: Hata kodu (ErrorCode enum)
        message: Kullanıcıya gösterilecek mesaj
        suggestion: Kullanıcıya önerilen aksiyon
        details: Teknik detaylar (opsiyonel, debug için)
        status_code: HTTP status kodu
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        suggestion: Optional[str] = None,
        details: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.details = details
        self.status_code = status_code
        super().__init__(message)

    def to_dict(self) -> dict:
        """Hata bilgisini dict formatına çevirir."""
        error_dict = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.suggestion:
            error_dict["suggestion"] = self.suggestion
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class ProviderError(AthenaError):
    """Dış kaynak (API provider) hataları.

    Semantic Scholar, OpenAlex gibi servislerdeki hatalar için kullanılır.
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.PROVIDER_UNAVAILABLE,
        message: str = "Dış servis şu anda kullanılamıyor",
        suggestion: str = "Lütfen birkaç dakika sonra tekrar deneyin",
        details: Optional[str] = None,
        status_code: int = 503,
    ) -> None:
        super().__init__(code, message, suggestion, details, status_code)


class LibraryError(AthenaError):
    """Kütüphane yönetimi hataları.

    Makale ekleme, silme, güncelleme işlemlerindeki hatalar için kullanılır.
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.LIBRARY_NOT_FOUND,
        message: str = "Kütüphane işlemi başarısız",
        suggestion: Optional[str] = None,
        details: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(code, message, suggestion, details, status_code)


class ValidationError(AthenaError):
    """Veri doğrulama hataları.

    İstek parametreleri veya veri formatı hataları için kullanılır.
    """

    def __init__(
        self,
        message: str = "Geçersiz veri formatı",
        suggestion: str = "Lütfen girdiğiniz verileri kontrol edin",
        details: Optional[str] = None,
        status_code: int = 422,
    ) -> None:
        super().__init__(
            ErrorCode.VALIDATION_ERROR, message, suggestion, details, status_code
        )


class DownloadError(AthenaError):
    """PDF indirme hataları.

    İndirme işlemlerindeki hatalar için kullanılır.
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.DOWNLOAD_FAILED,
        message: str = "PDF indirme başarısız",
        suggestion: str = "PDF kaynağı erişilebilir olmayabilir",
        details: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(code, message, suggestion, details, status_code)
