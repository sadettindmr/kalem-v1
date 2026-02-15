from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from athena.api.v2.routers import library, search, settings as settings_router, system
from athena.core.config import get_settings
from athena.core.exceptions import AthenaError, ErrorCode
from athena.core.file_paths import resolve_data_file_path
from athena.core.logging import get_request_id, setup_logging
from athena.core.middleware import RequestLoggingMiddleware

# Logging'i başlat (uygulama yüklenmeden önce)
setup_logging()

app = FastAPI(
    title="Kalem - Kasghar",
    description="Modular Monolith Backend API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Request Logging Middleware (CORS'tan önce eklenmeli)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware - Frontend React portuna izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:5173",  # Vite development server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(system.router, prefix="/api/v2")
app.include_router(settings_router.router, prefix="/api/v2")
app.include_router(search.router, prefix="/api/v2")
app.include_router(library.router, prefix="/api/v2")

# PDF dosyalari icin base directory
settings = get_settings()
data_dir = Path(settings.data_dir)
data_dir.mkdir(parents=True, exist_ok=True)


@app.get("/files/{requested_path:path}")
async def serve_pdf_file(requested_path: str) -> FileResponse:
    """Indirilen PDF dosyalarini guvenli sekilde servis eder."""
    resolved = resolve_data_file_path(requested_path, data_dir)
    if not resolved:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=resolved,
        media_type="application/pdf",
        filename=resolved.name,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def _get_request_id_from_context(request: Request) -> str | None:
    """Request ID'yi context veya request state'den alır."""
    # Önce context'ten dene
    request_id = get_request_id()
    if request_id:
        return request_id

    # Request state'den dene (middleware tarafından eklenir)
    if hasattr(request, "state") and hasattr(request.state, "request_id"):
        return request.state.request_id

    return None


# ============================================================================
# Global Exception Handlers
# ============================================================================


@app.exception_handler(AthenaError)
async def athena_error_handler(request: Request, exc: AthenaError) -> JSONResponse:
    """Kalem - Kasghar özel hatalarını yakalar ve standart formatta döner."""
    request_id = _get_request_id_from_context(request)

    logger.warning(
        f"AthenaError: {exc.code.value} - {exc.message}",
        extra={"path": request.url.path, "details": exc.details},
    )

    error_dict = exc.to_dict()
    if request_id:
        error_dict["request_id"] = request_id

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_dict,
        },
    )

    if request_id:
        response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """HTTP hatalarını yakalar ve standart formatta döner."""
    request_id = _get_request_id_from_context(request)

    logger.warning(
        f"HTTPException: {exc.status_code} - {exc.detail}",
        extra={"path": request.url.path},
    )

    # HTTP status koduna göre uygun hata kodu belirle
    error_code = ErrorCode.INTERNAL_ERROR.value
    if exc.status_code == 404:
        error_code = ErrorCode.NOT_FOUND.value
    elif exc.status_code == 422:
        error_code = ErrorCode.VALIDATION_ERROR.value

    error_content: dict = {
        "code": error_code,
        "message": str(exc.detail),
    }

    if request_id:
        error_content["request_id"] = request_id

    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": error_content,
        },
    )

    if request_id:
        response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pydantic doğrulama hatalarını yakalar ve kullanıcı dostu formatta döner."""
    request_id = _get_request_id_from_context(request)

    # Hataları okunabilir formata çevir
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"])
        errors.append(f"{loc}: {error['msg']}")

    error_details = "; ".join(errors)

    logger.warning(
        f"ValidationError: {error_details}",
        extra={"path": request.url.path},
    )

    error_content: dict = {
        "code": ErrorCode.VALIDATION_ERROR.value,
        "message": "İstek verisi doğrulanamadı",
        "suggestion": "Lütfen gönderdiğiniz verileri kontrol edin",
        "details": error_details,
    }

    if request_id:
        error_content["request_id"] = request_id

    response = JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": error_content,
        },
    )

    if request_id:
        response.headers["X-Request-ID"] = request_id

    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Beklenmeyen hataları yakalar ve 500 Internal Server Error döner."""
    request_id = _get_request_id_from_context(request)

    logger.error(
        f"Unexpected error: {type(exc).__name__} - {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True,
    )

    error_content: dict = {
        "code": ErrorCode.INTERNAL_ERROR.value,
        "message": "Beklenmeyen bir hata oluştu",
        "suggestion": "Lütfen daha sonra tekrar deneyin",
    }

    if request_id:
        error_content["request_id"] = request_id

    response = JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": error_content,
        },
    )

    if request_id:
        response.headers["X-Request-ID"] = request_id

    return response


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Kalem - Kasghar API",
        "version": "2.0.0",
        "docs": "/docs",
    }
