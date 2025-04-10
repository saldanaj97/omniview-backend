"""
Logging configuration for the OmniView Backend.
"""

import logging
import os
import sys
from typing import Dict, List, Optional


def configure_logging(
    log_level: str = "INFO",
    enable_json_logs: bool = False,
    quiet_loggers: Optional[List[str]] = None,
) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: The log level to use. Defaults to INFO.
        enable_json_logs: Whether to enable JSON logs. Defaults to False.
        quiet_loggers: List of logger names to set to ERROR level. Defaults to ["httpx", "httpcore"].
    """
    if quiet_loggers is None:
        quiet_loggers = ["httpx", "httpcore"]

    # Get log level from environment or parameter
    level = os.getenv("LOG_LEVEL", log_level).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    # Use JSON formatter for production or if explicitly enabled
    if enable_json_logs or os.getenv("ENABLE_JSON_LOGS", "").lower() == "true":
        _configure_json_logging(numeric_level)
    else:
        _configure_standard_logging(numeric_level)

    # Set quiet loggers
    for logger_name in quiet_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


def _configure_standard_logging(log_level: int) -> None:
    """
    Configure standard logging with a more readable format.
    """
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def _configure_json_logging(log_level: int) -> None:
    """
    Configure JSON logging for better integration with log management systems.

    Requires the python-json-logger package:
    pip install python-json-logger
    """
    try:
        from pythonjsonlogger import jsonlogger

        log_handler = logging.StreamHandler()
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(funcName)s %(lineno)s"
        )
        log_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(log_handler)

        # Remove default handlers
        for handler in root_logger.handlers[:]:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler is not log_handler
            ):
                root_logger.removeHandler(handler)

    except ImportError:
        print(
            "Warning: python-json-logger package not found. Falling back to standard logging."
        )
        _configure_standard_logging(log_level)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: The name of the logger.

    Returns:
        A Logger instance.
    """
    return logging.getLogger(name)
