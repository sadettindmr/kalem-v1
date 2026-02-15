from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from athena.core.config import get_settings as get_env_settings
from athena.models.settings import DEFAULT_ENABLED_PROVIDERS, UserSettings

ALLOWED_PROVIDERS = set(DEFAULT_ENABLED_PROVIDERS)


@dataclass
class UpdateSettingsData:
    openai_api_key: str | None = None
    semantic_scholar_api_key: str | None = None
    core_api_key: str | None = None
    openalex_email: str | None = None
    enabled_providers: list[str] | None = None
    proxy_url: str | None = None
    proxy_enabled: bool | None = None


class UserSettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self) -> UserSettings:
        """Ayar kaydini getirir; yoksa .env degerlerinden olusturur."""
        result = await self.db.execute(select(UserSettings).order_by(UserSettings.id.asc()))
        settings_row = result.scalars().first()
        if settings_row:
            return settings_row

        env = get_env_settings()
        settings_row = UserSettings(
            id=1,
            openai_api_key=env.openai_api_key or None,
            semantic_scholar_api_key=env.semantic_scholar_api_key or None,
            core_api_key=env.core_api_key or None,
            openalex_email=env.openalex_email or None,
            enabled_providers=list(DEFAULT_ENABLED_PROVIDERS),
            proxy_url=env.outbound_proxy or None,
            proxy_enabled=bool(env.outbound_proxy),
        )
        self.db.add(settings_row)
        await self.db.flush()
        return settings_row

    async def update_settings(self, data: UpdateSettingsData) -> UserSettings:
        settings_row = await self.get_settings()

        if data.openai_api_key is not None:
            settings_row.openai_api_key = self._normalize_secret_update(
                data.openai_api_key, settings_row.openai_api_key
            )
        if data.semantic_scholar_api_key is not None:
            settings_row.semantic_scholar_api_key = self._normalize_secret_update(
                data.semantic_scholar_api_key, settings_row.semantic_scholar_api_key
            )
        if data.core_api_key is not None:
            settings_row.core_api_key = self._normalize_secret_update(
                data.core_api_key, settings_row.core_api_key
            )
        if data.openalex_email is not None:
            settings_row.openalex_email = data.openalex_email.strip() or None
        if data.enabled_providers is not None:
            settings_row.enabled_providers = self._normalize_providers(data.enabled_providers)
        if data.proxy_url is not None:
            settings_row.proxy_url = data.proxy_url.strip() or None
        if data.proxy_enabled is not None:
            settings_row.proxy_enabled = data.proxy_enabled

        await self.db.flush()
        return settings_row

    def _normalize_secret_update(
        self, candidate: str | None, current_value: str | None
    ) -> str | None:
        if candidate is None:
            return current_value
        value = candidate.strip()
        if not value:
            return None
        if value.endswith("***"):
            return current_value
        return value

    def _normalize_providers(self, providers: list[str]) -> list[str]:
        normalized: list[str] = []
        for provider in providers:
            key = provider.strip().lower()
            if not key:
                continue
            if key not in ALLOWED_PROVIDERS:
                continue
            if key not in normalized:
                normalized.append(key)
        return normalized or list(DEFAULT_ENABLED_PROVIDERS)

