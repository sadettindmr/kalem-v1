from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from athena.core.database import get_db
from athena.services.settings import UpdateSettingsData, UserSettingsService

router = APIRouter(prefix="/system", tags=["System"])


class UserSettingsResponse(BaseModel):
    id: int
    openai_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    core_api_key: str | None = None
    openalex_email: str | None = None
    enabled_providers: list[str]
    proxy_url: str | None = None
    proxy_enabled: bool


class UserSettingsUpdateRequest(BaseModel):
    openai_api_key: SecretStr | None = Field(default=None)
    semantic_scholar_api_key: SecretStr | None = Field(default=None)
    core_api_key: SecretStr | None = Field(default=None)
    openalex_email: str | None = Field(default=None)
    enabled_providers: list[str] | None = Field(default=None)
    proxy_url: str | None = Field(default=None)
    proxy_enabled: bool | None = Field(default=None)


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


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(db: AsyncSession = Depends(get_db)) -> UserSettingsResponse:
    service = UserSettingsService(db)
    row = await service.get_settings()
    return _to_response(row)


@router.put("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    payload: UserSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
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

