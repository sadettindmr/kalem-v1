"""Standart hata yanıt şemaları."""

from typing import Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Hata detay şeması."""

    code: str
    message: str
    suggestion: Optional[str] = None
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standart hata yanıt şeması.

    TDD Bölüm 5 formatına uygun.
    """

    success: bool = False
    error: ErrorDetail
