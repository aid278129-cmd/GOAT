import logging
import time
import uuid
import sys
from contextvars import ContextVar
from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable to hold request_id across async calls
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class StructuredFormatter(logging.Formatter):
    """Structured log formatter including request ID, module, and timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        record.request_id = request_id_ctx.get()
        return super().format(record)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure system logger for auditable and privacy-conscious compliance records."""
    logger = logging.getLogger("zyntrix")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = StructuredFormatter(
            fmt="%(asctime)s [%(levelname)s] [req:%(request_id)s] %(name)s (%(filename)s:%(lineno)d) - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request-id tracing, timing, and security headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        token = request_id_ctx.set(req_id)
        start_time = time.perf_counter()

        logger.info(f"Incoming request: {request.method} {request.url.path}")

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"
            logger.info(
                f"Completed: {request.method} {request.url.path} -> Status {response.status_code} ({duration_ms:.2f}ms)"
            )
            return response
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Unhandled Exception in {request.method} {request.url.path}: {exc} ({duration_ms:.2f}ms)",
                exc_info=True,
            )
            raise
        finally:
            request_id_ctx.reset(token)
