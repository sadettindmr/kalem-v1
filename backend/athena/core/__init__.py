"""Core modulleri - config, database, exceptions, logging, middleware.

Not:
- Alembic gibi sadece config/database import eden akislarda tum runtime
  bagimliliklarinin (or. loguru) yuklenmesi zorunlu olmasin diye
  logging/middleware importlari kosullu tutulur.
"""

from athena.core.config import Settings, get_settings
from athena.core.database import get_db
from athena.core.exceptions import (
    AthenaError,
    DownloadError,
    ErrorCode,
    LibraryError,
    ProviderError,
    ValidationError,
)

try:
    from athena.core.logging import (
        clear_request_id,
        get_request_id,
        set_request_id,
        setup_logging,
    )
    from athena.core.middleware import RequestLoggingMiddleware
except ModuleNotFoundError:
    # Alembic/env gibi lightweight import akislari icin.
    clear_request_id = None
    get_request_id = None
    set_request_id = None
    setup_logging = None
    RequestLoggingMiddleware = None

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Database
    "get_db",
    # Exceptions
    "AthenaError",
    "DownloadError",
    "ErrorCode",
    "LibraryError",
    "ProviderError",
    "ValidationError",
    # Logging
    "clear_request_id",
    "get_request_id",
    "set_request_id",
    "setup_logging",
    # Middleware
    "RequestLoggingMiddleware",
]
