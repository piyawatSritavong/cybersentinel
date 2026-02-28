import asyncio
import time
import logging
from typing import Callable, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are rejected immediately
    - HALF_OPEN: After recovery timeout, allow a single probe request
    """

    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half_open"

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = self.STATE_CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._success_count = 0

    @property
    def state(self) -> str:
        if self._state == self.STATE_OPEN:
            if self._last_failure_time and (
                time.time() - self._last_failure_time >= self.recovery_timeout
            ):
                self._state = self.STATE_HALF_OPEN
        return self._state

    def record_success(self):
        self._failure_count = 0
        self._success_count += 1
        if self._state == self.STATE_HALF_OPEN:
            self._state = self.STATE_CLOSED
            logger.info(f"[CIRCUIT-BREAKER:{self.name}] Circuit CLOSED after successful probe")

    def record_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = self.STATE_OPEN
            logger.warning(
                f"[CIRCUIT-BREAKER:{self.name}] Circuit OPEN after {self._failure_count} failures"
            )

    def allow_request(self) -> bool:
        current = self.state
        if current == self.STATE_CLOSED:
            return True
        if current == self.STATE_HALF_OPEN:
            return True
        return False

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


_circuit_breakers: dict = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
) -> CircuitBreaker:
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _circuit_breakers[name]


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker_name: Optional[str] = None,
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cb = None
            if circuit_breaker_name:
                cb = get_circuit_breaker(circuit_breaker_name)

            last_exception = None
            for attempt in range(max_retries + 1):
                if cb and not cb.allow_request():
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{circuit_breaker_name}' is open. "
                        f"Service unavailable."
                    )

                try:
                    result = await func(*args, **kwargs)
                    if cb:
                        cb.record_success()
                    return result
                except retryable_exceptions as e:
                    last_exception = e
                    if cb:
                        cb.record_failure()

                    if attempt < max_retries:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay,
                        )
                        logger.warning(
                            f"[RESILIENCE] {func.__name__} attempt {attempt + 1}/{max_retries + 1} "
                            f"failed: {e}. Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"[RESILIENCE] {func.__name__} exhausted all {max_retries + 1} attempts. "
                            f"Last error: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


async def resilient_call(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    circuit_breaker_name: Optional[str] = None,
    **kwargs,
):
    cb = None
    if circuit_breaker_name:
        cb = get_circuit_breaker(circuit_breaker_name)

    last_exception = None
    for attempt in range(max_retries + 1):
        if cb and not cb.allow_request():
            raise CircuitBreakerOpen(
                f"Circuit breaker '{circuit_breaker_name}' is open."
            )

        try:
            result = await func(*args, **kwargs)
            if cb:
                cb.record_success()
            return result
        except Exception as e:
            last_exception = e
            if cb:
                cb.record_failure()

            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), 30.0)
                logger.warning(
                    f"[RESILIENCE] Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)

    raise last_exception
