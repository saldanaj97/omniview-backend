"""
Redis cache logger module.
"""

from typing import Any, Dict, Optional

from app.utils.logging.config import get_logger


class RedisLogger:
    """
    Logging utility for Redis cache operations.
    Provides structured logging for Redis operations with consistent formatting.
    """

    def __init__(self, name: str = "redis_cache"):
        self.logger = get_logger(name)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional extra data."""
        if kwargs:
            self.logger.info("%s - %s", message, self._format_kwargs(kwargs))
        else:
            self.logger.info(message)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional extra data."""
        if kwargs:
            self.logger.debug("%s - %s", message, self._format_kwargs(kwargs))
        else:
            self.logger.debug(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional extra data."""
        if kwargs:
            self.logger.warning("%s - %s", message, self._format_kwargs(kwargs))
        else:
            self.logger.warning(message)

    def error(
        self, message: str, exception: Optional[Exception] = None, **kwargs: Any
    ) -> None:
        """Log error message with optional exception and extra data."""
        if exception:
            if kwargs:
                self.logger.error(
                    "%s - %s - %s: %s",
                    message,
                    self._format_kwargs(kwargs),
                    type(exception).__name__,
                    str(exception),
                    exc_info=True,
                )
            else:
                self.logger.error(
                    "%s - %s: %s",
                    message,
                    type(exception).__name__,
                    str(exception),
                    exc_info=True,
                )
        elif kwargs:
            self.logger.error("%s - %s", message, self._format_kwargs(kwargs))
        else:
            self.logger.error(message)

    def _format_kwargs(self, kwargs: Dict[str, Any]) -> str:
        """Format kwargs as a string for logging."""
        return ", ".join(f"{key}={repr(value)}" for key, value in kwargs.items())
