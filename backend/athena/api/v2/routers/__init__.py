from athena.api.v2.routers.library import router as library_router
from athena.api.v2.routers.search import router as search_router
from athena.api.v2.routers.settings import router as settings_router
from athena.api.v2.routers.system import router as system_router

__all__ = [
    "library_router",
    "search_router",
    "settings_router",
    "system_router",
]
