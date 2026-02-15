"""Request logging middleware.

Sprint 4.2 - Her HTTP isteği için:
- Unique request_id (UUID) oluşturur
- İstek süresini (process_time) ölçer
- Detaylı log kaydı tutar
"""

import time
import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from athena.core.logging import clear_request_id, set_request_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """HTTP request/response loglama middleware'i.

    Her istek için:
    - Unique request_id (UUID4) oluşturur
    - İstek süresini milisaniye olarak hesaplar
    - Başarılı ve başarısız istekleri loglar
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Request ID oluştur
        request_id = str(uuid.uuid4())
        set_request_id(request_id)

        # Request state'e de ekle (exception handler'lar için)
        request.state.request_id = request_id

        # 2. Client IP
        client_ip = self._get_client_ip(request)

        # 3. Başlangıç zamanı
        start_time = time.perf_counter()

        # 4. İsteği işle
        try:
            response = await call_next(request)

            # 5. Süre hesapla (ms)
            process_time = (time.perf_counter() - start_time) * 1000

            # 6. Response header'a request_id ekle
            response.headers["X-Request-ID"] = request_id

            # 7. Log kaydı
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time, 2),
                client_ip=client_ip,
            )

            return response

        except Exception as exc:
            # Hata durumunda da loglama yap
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed with exception",
                method=request.method,
                path=request.url.path,
                process_time_ms=round(process_time, 2),
                client_ip=client_ip,
                error=str(exc),
            )
            raise

        finally:
            # Context'i temizle
            clear_request_id()

    def _get_client_ip(self, request: Request) -> str:
        """Client IP adresini döner.

        Proxy arkasındaysa X-Forwarded-For header'ını kontrol eder.
        """
        # X-Forwarded-For header (proxy arkasında)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # İlk IP gerçek client IP'sidir
            return forwarded_for.split(",")[0].strip()

        # X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Direkt bağlantı
        if request.client:
            return request.client.host

        return "unknown"
