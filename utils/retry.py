"""
MCP Retry Handler

Handles retry logic with exponential backoff using proven patterns
from the working DirectMCPClient implementation.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from .exceptions import MCPRetryError

logger = logging.getLogger(__name__)


class MCPRetryHandler:
    """
    Handles retry logic with exponential backoff.

    Extracted from proven retry patterns in DirectMCPClient.call_github_tools()
    to ensure compatibility with working retry strategies.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 30.0,
        retryable_exceptions: tuple[type[Exception], ...] = None,
    ):
        """
        Initialize retry handler.

        Args:
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds (used for exponential backoff)
            max_delay: Maximum delay between retries
            retryable_exceptions: Tuple of exception types that should trigger retries
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

        # Default retryable exceptions based on working patterns
        if retryable_exceptions is None:
            self.retryable_exceptions = (
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
                # Add other network-related exceptions that should be retried
            )
        else:
            self.retryable_exceptions = retryable_exceptions

    async def with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Execute operation with exponential backoff retry.

        This implementation follows the exact pattern from
        DirectMCPClient.call_github_tools() retry logic.

        Args:
            operation: Async callable to execute
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result from successful operation execution

        Raises:
            MCPRetryError: If all retry attempts are exhausted
            Exception: If operation fails with non-retryable exception
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"Executing operation (attempt {attempt + 1}/{self.max_retries})"
                )

                result = await operation(*args, **kwargs)

                if attempt > 0:
                    logger.info(f"Operation succeeded on attempt {attempt + 1}")

                return result

            except Exception as e:
                last_error = e

                if not self.should_retry(e):
                    logger.error(f"Non-retryable error: {e}")
                    raise e

                if attempt < self.max_retries - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Network error on attempt {attempt + 1}, "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Failed after {self.max_retries} attempts: {e}")

        # If we get here, all retries were exhausted
        raise MCPRetryError(
            f"Operation failed after {self.max_retries} retry attempts",
            attempts=self.max_retries,
            last_error=last_error,
        )

    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if exception is retryable.

        Args:
            exception: Exception that occurred

        Returns:
            True if exception should trigger a retry
        """
        return isinstance(exception, self.retryable_exceptions)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay with exponential backoff.

        This uses the exact pattern from DirectMCPClient:
        wait_time = 2 ** attempt  # Exponential backoff

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: 2^attempt
        delay = self.base_delay**attempt

        # Cap at maximum delay
        delay = min(delay, self.max_delay)

        return delay

    async def with_retry_and_cleanup(
        self, operation: Callable, cleanup_func: Callable = None, *args, **kwargs
    ) -> Any:
        """
        Execute operation with retry and guaranteed cleanup.

        This pattern is extracted from DirectMCPClient where cleanup
        is performed in the finally block regardless of success/failure.

        Args:
            operation: Async callable to execute
            cleanup_func: Optional cleanup function to call after operation
            *args: Arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation

        Returns:
            Result from successful operation execution
        """
        try:
            return await self.with_retry(operation, *args, **kwargs)
        finally:
            if cleanup_func:
                try:
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func()
                    else:
                        cleanup_func()
                except Exception as cleanup_error:
                    logger.warning(f"Cleanup function failed: {cleanup_error}")


class TimedRetryHandler(MCPRetryHandler):
    """
    Retry handler that tracks timing information for monitoring.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execution_times = []
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0

    async def with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry and timing tracking."""
        start_time = time.time()
        attempts_made = 0

        try:
            result = await super().with_retry(operation, *args, **kwargs)
            self.total_successes += 1
            return result
        except Exception as e:
            self.total_failures += 1
            raise e
        finally:
            end_time = time.time()
            execution_time = end_time - start_time
            self.execution_times.append(execution_time)
            self.total_attempts += attempts_made

    def get_stats(self) -> dict:
        """Get retry handler statistics."""
        if not self.execution_times:
            return {
                "total_operations": 0,
                "total_attempts": 0,
                "success_rate": 0.0,
                "avg_execution_time": 0.0,
                "total_successes": 0,
                "total_failures": 0,
            }

        return {
            "total_operations": len(self.execution_times),
            "total_attempts": self.total_attempts,
            "success_rate": self.total_successes
            / (self.total_successes + self.total_failures),
            "avg_execution_time": sum(self.execution_times) / len(self.execution_times),
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
        }


async def retry_with_exponential_backoff(
    operation: Callable, max_retries: int = 3, base_delay: float = 2.0, *args, **kwargs
) -> Any:
    """
    Standalone function for simple retry operations.

    Args:
        operation: Async callable to execute
        max_retries: Maximum retry attempts
        base_delay: Base delay for exponential backoff
        *args: Arguments for operation
        **kwargs: Keyword arguments for operation

    Returns:
        Result from successful operation
    """
    handler = MCPRetryHandler(max_retries=max_retries, base_delay=base_delay)
    return await handler.with_retry(operation, *args, **kwargs)
