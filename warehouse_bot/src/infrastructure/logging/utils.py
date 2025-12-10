"""
Утилиты для логирования действий пользователя и сервера.
"""

import structlog
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(str, Enum):
    """Уровни логирования."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Logger:
    """Обертка для структурированного логирования."""
    
    def __init__(self, name: str):
        self._logger = structlog.get_logger(name)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Логирование отладочной информации."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Логирование информационных сообщений."""
        self._logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Логирование предупреждений."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Логирование ошибок."""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs: Any) -> None:
        """Логирование критических ошибок."""
        self._logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs: Any) -> None:
        """Логирование исключений."""
        self._logger.exception(message, **kwargs)


def get_logger(name: str) -> Logger:
    """Возвращает настроенный логгер."""
    return Logger(name)


def log_user_action(
    logger: Logger,
    user_id: int,
    action: str,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
    **kwargs: Any
) -> None:
    """Логирует действия пользователя."""
    logger.info(
        "Пользовательское действие",
        user_id=user_id,
        action=action,
        chat_id=chat_id,
        message_id=message_id,
        **kwargs
    )


def log_server_action(
    logger: Logger,
    action: str,
    result: Optional[str] = None,
    duration: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Логирует действия сервера."""
    logger.info(
        "Серверное действие",
        action=action,
        result=result,
        duration=duration,
        **kwargs
    )


def log_error(
    logger: Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> None:
    """Логирует ошибки."""
    log_context = context or {}
    log_context.update(kwargs)
    
    logger.error(
        str(error),
        error_type=type(error).__name__,
        error_message=str(error),
        **log_context
    )


def log_warning(
    logger: Logger,
    message: str,
    **kwargs: Any
) -> None:
    """Логирует предупреждения."""
    logger.warning(
        message,
        **kwargs
    )