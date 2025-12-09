import json
import logging
import sys
from typing import Dict, Any

import structlog

from ...config.settings import settings


def setup_logging():
    """
    Настраивает логирование приложения.
    """
    # Определяем формат логирования на основе настроек
    if settings.log_format.upper() == "JSON":
        # JSON формат для production
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(serializer=json.dumps)
        ]
    else:
        # Консольный формат для разработки
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer()
        ]
    
    # Настройка structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Настройка стандартного логгера
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level),
        stream=sys.stdout,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Возвращает настроенный логгер.
    
    Args:
        name: Имя логгера
        
    Returns:
        structlog.BoundLogger: Настроенный логгер
    """
    return structlog.get_logger(name)


def log_exception(exc: Exception, context: Dict[str, Any] = None):
    """
    Логирует исключение с контекстом.
    
    Args:
        exc: Исключение для логирования
        context: Дополнительный контекст
    """
    logger = get_logger(__name__)
    logger.exception(
        "Произошло исключение",
        exc_info=exc,
        **(context or {})
    )