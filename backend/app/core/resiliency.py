import asyncio
import logging
import functools
from typing import Callable, Any

logger = logging.getLogger(__name__)

class CircuitBreakerError(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False
        
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(f"Circuit breaker tripped after {self.failure_count} failures!")

    def record_success(self):
        self.failure_count = 0
        self.is_open = False
        
    def check_state(self):
        if self.is_open:
            now = asyncio.get_event_loop().time()
            if now - self.last_failure_time > self.recovery_timeout:
                self.is_open = False # Half-open
                self.failure_count = 0
            else:
                raise CircuitBreakerError("Circuit breaker is open. Fast failing request.")

def with_retry(max_retries: int = 2, base_delay: float = 1.0, exceptions=(Exception,)):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    delay = base_delay * (2 ** (retries - 1))
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} in {delay}s due to: {e}")
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

def with_timeout(timeout_seconds: float):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s")
                raise
        return wrapper
    return decorator
