"""Standart hata yanıt şemaları."""

from typing import Optional

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Hata detay şeması."""

    code: str = Field(
        ...,
        description="Hata kodu (VALIDATION_ERROR, NOT_FOUND, INTERNAL_ERROR vb.)",
        examples=["VALIDATION_ERROR"],
    )
    message: str = Field(
        ...,
        description="Kullanıcı dostu hata mesajı",
        examples=["İstek verisi doğrulanamadı"],
    )
    suggestion: Optional[str] = Field(
        default=None,
        description="Hatayı çözmek için öneri",
        examples=["Lütfen gönderdiğiniz verileri kontrol edin"],
    )
    details: Optional[str] = Field(
        default=None,
        description="Teknik hata detayları",
        examples=["body -> query: field required"],
    )


class ErrorResponse(BaseModel):
    """Standart hata yanıt şeması."""

    success: bool = Field(
        default=False,
        description="İşlem başarılı mı (hatalar için her zaman false)",
    )
    error: ErrorDetail = Field(
        ...,
        description="Hata detayları",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": False,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "İstek verisi doğrulanamadı",
                        "suggestion": "Lütfen gönderdiğiniz verileri kontrol edin",
                        "details": "body -> query: field required",
                    },
                }
            ]
        }
    }
