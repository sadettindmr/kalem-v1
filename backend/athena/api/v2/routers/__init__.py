from athena.api.v2.routers.library import router as library_router
from athena.api.v2.routers.search import router as search_router
from athena.api.v2.routers.system import router as system_router

__all__ = [
    "library_router",
    "search_router",
    "system_router",
]
