import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text

from athena.core.config import get_settings
from athena.core.database import engine

router = APIRouter(tags=["System"])
settings = get_settings()

# Reset endpoint için sabit değer
RESET_CONFIRMATION_STRING = "DELETE-ALL-DATA"


class ResetRequest(BaseModel):
    """Sistem sıfırlama isteği."""

    confirmation: str


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Checks database and Redis connectivity.
    Returns 200 if all services are healthy, 503 otherwise.
    """
    health_status = {
        "status": "healthy",
        "database": "connected",
        "redis": "connected",
        "version": "2.0.0",
    }

    # Check database connection
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"

    # Check Redis connection
    try:
        redis_client = Redis.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.aclose()
    except Exception:
        health_status["status"] = "unhealthy"
        health_status["redis"] = "disconnected"

    if health_status["status"] == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )

    return health_status


@router.post("/system/reset")
async def reset_system(request: ResetRequest):
    """Sistemi fabrika ayarlarına döndürür.

    DİKKAT: Bu işlem geri alınamaz! Tüm veriler silinir.

    Args:
        request: confirmation alanı "DELETE-ALL-DATA" olmalı

    Returns:
        Silinen dosya sayısı ile başarı mesajı

    Raises:
        HTTPException 403: Yanlış onay kodu
    """
    # 1. Güvenlik kontrolü
    if request.confirmation != RESET_CONFIRMATION_STRING:
        logger.warning(
            f"System reset attempted with wrong confirmation: {request.confirmation}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Geçersiz onay kodu. Sistemi sıfırlamak için 'DELETE-ALL-DATA' girin.",
        )

    logger.critical("SYSTEM RESET INITIATED - All data will be deleted!")

    # 2. Veritabanı tablolarını temizle (CASCADE ile)
    tables_to_truncate = [
        "library_tags",  # Association table first
        "paper_authors",  # Association table
        "library_entries",
        "papers",
        "authors",
        "tags",
    ]

    async with engine.begin() as conn:
        for table in tables_to_truncate:
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                logger.critical(f"Truncated table: {table}")
            except Exception as e:
                logger.error(f"Error truncating table {table}: {e}")

    logger.critical("Database tables truncated successfully")

    # 3. PDF dosyalarını sil
    deleted_files_count = 0
    data_dir = Path(settings.data_dir)

    if data_dir.exists():
        try:
            # Klasör içindeki tüm dosya ve alt klasörleri say ve sil
            for item in data_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    deleted_files_count += 1
                elif item.is_dir():
                    # Alt klasördeki dosyaları say
                    for sub_item in item.rglob("*"):
                        if sub_item.is_file():
                            deleted_files_count += 1
                    # Alt klasörü tamamen sil
                    shutil.rmtree(item)

            logger.critical(f"Deleted {deleted_files_count} files from {data_dir}")
        except Exception as e:
            logger.error(f"Error cleaning data directory: {e}")

    logger.critical("SYSTEM RESET COMPLETED")

    return {
        "status": "system_reset_completed",
        "deleted_files_count": deleted_files_count,
    }
