"""Loguru ile yapılandırılmış loglama modülü.

Sprint 4.2 - Structured Logging
- Production: JSON format
- Development: Renkli console output
- Request correlation ID desteği
"""

import sys
from contextvars import ContextVar
from typing import Any

from loguru import logger

from athena.core.config import get_settings

# Request ID için context variable (async-safe)
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    """Mevcut request'in ID'sini döner."""
    return request_id_ctx.get()


def set_request_id(request_id: str) -> None:
    """Request ID'yi context'e set eder."""
    request_id_ctx.set(request_id)


def clear_request_id() -> None:
    """Request ID'yi temizler."""
    request_id_ctx.set(None)


def request_id_filter(record: dict[str, Any]) -> bool:
    """Log kaydına request_id ekler."""
    record["extra"]["request_id"] = get_request_id() or "-"
    return True


def setup_logging() -> None:
    """Loguru yapılandırmasını başlatır.

    - debug=True (Development): Renkli console output
    - debug=False (Production): JSON format
    """
    settings = get_settings()

    # Mevcut handler'ları temizle
    logger.remove()

    if settings.debug:
        # Development: Renkli console output
        logger.add(
            sys.stderr,
            level=settings.log_level.upper(),
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{extra[request_id]}</cyan> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            filter=request_id_filter,
            colorize=True,
        )
    else:
        # Production: JSON format
        logger.add(
            sys.stderr,
            level=settings.log_level.upper(),
            format="{message}",
            filter=request_id_filter,
            serialize=True,  # JSON output
        )

    logger.info(
        f"Logging configured: level={settings.log_level}, mode={'development' if settings.debug else 'production'}"
    )
