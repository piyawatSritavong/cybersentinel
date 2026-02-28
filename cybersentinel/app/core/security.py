import hmac
import time
import logging
from typing import Dict
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

_rate_limit_tracker: Dict[str, list] = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 120


def _check_rate_limit(client_key: str) -> bool:
    now = time.time()
    if client_key not in _rate_limit_tracker:
        _rate_limit_tracker[client_key] = []

    _rate_limit_tracker[client_key] = [
        ts for ts in _rate_limit_tracker[client_key]
        if now - ts < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_tracker[client_key]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    _rate_limit_tracker[client_key].append(now)
    return True


def _timing_safe_compare(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key header (X-API-KEY) missing",
        )

    if not settings.app_api_key:
        logger.error("APP_API_KEY is not set in environment variables!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API Key configuration missing",
        )

    key_prefix = api_key_header[:4] if len(api_key_header) >= 4 else "***"

    if not _check_rate_limit(key_prefix):
        logger.warning(f"Rate limit exceeded for key: {key_prefix}****")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )

    if _timing_safe_compare(api_key_header, settings.app_api_key):
        return api_key_header

    logger.warning(f"Invalid API Key attempt: {key_prefix}****")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid API Key",
    )
