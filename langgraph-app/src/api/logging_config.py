"""Structured logging configuration for production.

Features:
    - JSON formatting for log aggregation (ELK, Datadog, etc.)
    - Log rotation (daily, 30 days retention)
    - Different log levels per environment
    - Request ID tracking
    - Performance metrics
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from pythonjsonlogger import jsonlogger

from api.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["timestamp"] = self.formatTime(record, self.datefmt)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["environment"] = settings.environment

        # Add request context if available
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id


def setup_logging() -> None:
    """Configure structured logging for production.

    Sets up:
        - JSON formatter for file logs
        - Console handler for development
        - Rotating file handler (daily rotation, 30 days retention)
        - Different log levels per environment
    """
    # Create logs directory
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (text format for development)
    console_handler = logging.StreamHandler(sys.stdout)
    if settings.environment == "development":
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        console_handler.setFormatter(logging.Formatter(console_format))
    else:
        # JSON format for production console (Docker logs)
        console_handler.setFormatter(CustomJsonFormatter())
    root_logger.addHandler(console_handler)

    # File handler with rotation (production only)
    if settings.environment in ("staging", "production"):
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=settings.log_file,
            when="midnight",  # Rotate daily
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding="utf-8",
        )
        file_handler.setFormatter(CustomJsonFormatter())
        root_logger.addHandler(file_handler)

    # Configure structlog (optional, for structured logging)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
