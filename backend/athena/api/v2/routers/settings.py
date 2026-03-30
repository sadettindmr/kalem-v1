from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from athena.core.database import get_db
from athena.services.settings import UpdateSettingsData, UserSettingsService

router = APIRouter(prefix="/system", tags=["Settings"])


class UserSettingsResponse(BaseModel):
    """Kullanıcı ayarları yanıtı (API anahtarları maskelenmiş)."""

    id: int = Field(..., description="Ayar kaydı ID", examples=[1])
    openai_api_key: str | None = Field(default=None, description="OpenAI API anahtarı (maskelenmiş)", examples=["sk-***"])
    semantic_scholar_api_key: str | None = Field(default=None, description="Semantic Scholar API anahtarı (maskelenmiş)", examples=["***"])
    core_api_key: str | None = Field(default=None, description="CORE API anahtarı (maskelenmiş)", examples=["***"])
    openalex_email: str | None = Field(default=None, description="OpenAlex için iletişim e-postası", examples=["researcher@university.edu"])
    enabled_providers: list[str] = Field(..., description="Aktif arama sağlayıcıları", examples=[["semantic", "openalex", "arxiv", "crossref", "core"]])
    proxy_url: str | None = Field(default=None, description="Proxy sunucu URL'si", examples=["http://proxy.university.edu:8080"])
    proxy_enabled: bool = Field(..., description="Proxy aktif mi", examples=[False])


class UserSettingsUpdateRequest(BaseModel):
    """Kullanıcı ayarları güncelleme isteği (kısmi güncelleme destekli)."""

    openai_api_key: SecretStr | None = Field(default=None, description="OpenAI API anahtarı")
    semantic_scholar_api_key: SecretStr | None = Field(default=None, description="Semantic Scholar API anahtarı")
    core_api_key: SecretStr | None = Field(default=None, description="CORE API anahtarı")
    openalex_email: str | None = Field(default=None, description="OpenAlex iletişim e-postası", examples=["researcher@university.edu"])
    enabled_providers: list[str] | None = Field(default=None, description="Aktif sağlayıcı listesi", examples=[["semantic", "openalex", "arxiv"]])
    proxy_url: str | None = Field(default=None, description="Proxy sunucu URL'si", examples=["http://proxy.university.edu:8080"])
    proxy_enabled: bool | None = Field(default=None, description="Proxy aktif/pasif", examples=[True])


def _mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if "-" in normalized:
        return f"{normalized.split('-', 1)[0]}-***"
    return "***"


def _to_response(row) -> UserSettingsResponse:
    return UserSettingsResponse(
        id=row.id,
        openai_api_key=_mask_secret(row.openai_api_key),
        semantic_scholar_api_key=_mask_secret(row.semantic_scholar_api_key),
        core_api_key=_mask_secret(row.core_api_key),
        openalex_email=row.openalex_email,
        enabled_providers=row.enabled_providers or [],
        proxy_url=row.proxy_url,
        proxy_enabled=row.proxy_enabled,
    )


@router.get(
    "/settings",
    response_model=UserSettingsResponse,
    summary="Kullanıcı Ayarlarını Getir",
    response_description="Mevcut ayarlar (API anahtarları maskelenmiş)",
)
async def get_user_settings(db: AsyncSession = Depends(get_db)) -> UserSettingsResponse:
    """Mevcut kullanıcı ayarlarını döndürür.

    API anahtarları güvenlik için maskelenerek (`sk-***`) döner.
    İlk çağrıda `.env` dosyasından varsayılan ayarlar oluşturulur.
    """
    service = UserSettingsService(db)
    row = await service.get_settings()
    return _to_response(row)


@router.put(
    "/settings",
    response_model=UserSettingsResponse,
    summary="Kullanıcı Ayarlarını Güncelle",
    response_description="Güncellenen ayarlar (API anahtarları maskelenmiş)",
)
async def update_user_settings(
    payload: UserSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Kullanıcı ayarlarını kısmi (partial) günceller.

    Yalnızca gönderilen alanlar güncellenir, diğerleri korunur.
    API anahtarları, sağlayıcı listesi ve proxy ayarları bu endpoint ile yönetilir.
    """
    service = UserSettingsService(db)
    data = UpdateSettingsData(
        openai_api_key=payload.openai_api_key.get_secret_value()
        if payload.openai_api_key is not None
        else None,
        semantic_scholar_api_key=payload.semantic_scholar_api_key.get_secret_value()
        if payload.semantic_scholar_api_key is not None
        else None,
        core_api_key=payload.core_api_key.get_secret_value()
        if payload.core_api_key is not None
        else None,
        openalex_email=payload.openalex_email,
        enabled_providers=payload.enabled_providers,
        proxy_url=payload.proxy_url,
        proxy_enabled=payload.proxy_enabled,
    )
    row = await service.update_settings(data)
    return _to_response(row)

