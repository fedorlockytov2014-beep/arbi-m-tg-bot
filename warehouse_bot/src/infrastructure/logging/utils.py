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
    
    async def debug(self, message: str, **kwargs: Any) -> None:
        """Логирование отладочной информации."""
        await self._logger.debug(message, **kwargs)
    
    async def info(self, message: str, **kwargs: Any) -> None:
        """Логирование информационных сообщений."""
        await self._logger.info(message, **kwargs)
    
    async def warning(self, message: str, **kwargs: Any) -> None:
        """Логирование предупреждений."""
        await self._logger.warning(message, **kwargs)
    
    async def error(self, message: str, **kwargs: Any) -> None:
        """Логирование ошибок."""
        await self._logger.error(message, **kwargs)
    
    async def critical(self, message: str, **kwargs: Any) -> None:
        """Логирование критических ошибок."""
        await self._logger.critical(message, **kwargs)
    
    async def exception(self, message: str, **kwargs: Any) -> None:
        """Логирование исключений."""
        await self._logger.exception(message, **kwargs)


def get_logger(name: str) -> Logger:
    """Возвращает настроенный логгер."""
    return Logger(name)


async def log_user_action(
    logger: Logger,
    user_id: int,
    action: str,
    chat_id: Optional[int] = None,
    message_id: Optional[int] = None,
    **kwargs: Any
) -> None:
    """Логирует действия пользователя."""
    await logger.info(
        "Пользовательское действие",
        user_id=user_id,
        action=action,
        chat_id=chat_id,
        message_id=message_id,
        **kwargs
    )


async def log_server_action(
    logger: Logger,
    action: str,
    result: Optional[str] = None,
    duration: Optional[float] = None,
    **kwargs: Any
) -> None:
    """Логирует действия сервера."""
    await logger.info(
        "Серверное действие",
        action=action,
        result=result,
        duration=duration,
        **kwargs
    )


async def log_error(
    logger: Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> None:
    """Логирует ошибки."""
    log_context = context or {}
    log_context.update(kwargs)
    
    await logger.error(
        str(error),
        error_type=type(error).__name__,
        error_message=str(error),
        **log_context
    )


async def log_warning(
    logger: Logger,
    message: str,
    **kwargs: Any
) -> None:
    """Логирует предупреждения."""
    await logger.warning(
        message,
        **kwargs
    )