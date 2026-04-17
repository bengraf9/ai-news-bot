"""
Retry helpers for LLM providers.

Handles transient errors (rate limits, overloaded, service unavailable)
with exponential backoff. Designed to be used as a decorator on any
provider's generate() method.
"""
import time
import functools
from typing import Callable, Any
from ..logger import setup_logger


logger = setup_logger(__name__)


# HTTP status codes we should retry on
RETRY_STATUS_CODES = {429, 500, 502, 503, 529}


def _extract_status_code(exc: Exception) -> int | None:
    """
    Extract HTTP status code from various exception types.
    Returns None if no status code can be determined.
    """
    # Anthropic SDK exceptions have a .status_code attribute
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code

    # Google GenAI errors.APIError has a .code attribute
    code = getattr(exc, "code", None)
    if isinstance(code, int):
        return code

    # Some exceptions encode the code in the message: "Error code: 529 - ..."
    msg = str(exc)
    for sc in RETRY_STATUS_CODES:
        if f"code: {sc}" in msg or f"code {sc}" in msg or f"{sc} " in msg[:20]:
            return sc

    # Lowercase keyword fallbacks (Gemini's gRPC errors mention "RESOURCE_EXHAUSTED" / "UNAVAILABLE")
    msg_lower = msg.lower()
    if "resource_exhausted" in msg_lower or "rate limit" in msg_lower or "quota" in msg_lower or "too many requests" in msg_lower:
        return 429
    if "unavailable" in msg_lower or "overloaded" in msg_lower:
        return 503

    return None


def with_retries(
    max_attempts: int = 4,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
):
    """
    Decorator: retries a function on transient API errors with exponential backoff.

    Args:
        max_attempts: Total attempts including the first call (so max_attempts=4 = 1 try + 3 retries)
        base_delay: Initial backoff in seconds. Doubles each retry.
        max_delay: Cap on backoff delay per retry.

    Backoff sequence with defaults: 2s, 4s, 8s (capped at max_delay).
    Total worst-case wait before final failure: ~14s.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    status = _extract_status_code(e)

                    # Not a retryable error — re-raise immediately
                    if status not in RETRY_STATUS_CODES:
                        raise

                    # Last attempt — no point sleeping, just re-raise
                    if attempt >= max_attempts:
                        logger.error(
                            f"API call failed after {max_attempts} attempts "
                            f"(last error: HTTP {status}): {str(e)[:200]}"
                        )
                        raise

                    # Compute delay: exponential backoff with cap
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    logger.warning(
                        f"API call failed with HTTP {status} (attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)

            # Should never reach here, but just in case
            if last_exc:
                raise last_exc
            raise RuntimeError("Retry loop exited unexpectedly")
        return wrapper
    return decorator
