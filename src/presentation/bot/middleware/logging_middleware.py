import logging
import time
from typing import Any, Callable, Dict, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования входящих сообщений и callback'ов.
    """
    
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Подготовка данных для логирования
        if isinstance(event, Message):
            event_type = "message"
            chat_id = event.chat.id
            user_id = event.from_user.id
            message_id = event.message_id
            text = getattr(event, 'text', getattr(event, 'caption', ''))
            
            log_data = {
                "event_type": event_type,
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": message_id,
                "text": text
            }
        elif isinstance(event, CallbackQuery):
            event_type = "callback_query"
            chat_id = event.message.chat.id if event.message else None
            user_id = event.from_user.id
            callback_data = event.data
            
            log_data = {
                "event_type": event_type,
                "chat_id": chat_id,
                "user_id": user_id,
                "callback_data": callback_data
            }
        else:
            # Для других типов событий
            log_data = {
                "event_type": type(event).__name__,
                "event": str(event)
            }
        
        start_time = time.time()
        
        try:
            # Логируем получение события
            logger.info("Получено событие", **log_data)
            
            # Выполняем обработчик
            result = await handler(event, data)
            
            # Логируем успешную обработку
            processing_time = time.time() - start_time
            logger.info(
                "Событие успешно обработано",
                processing_time=processing_time,
                **log_data
            )
            
            return result
            
        except Exception as e:
            # Логируем ошибку
            processing_time = time.time() - start_time
            logger.error(
                "Ошибка при обработке события",
                processing_time=processing_time,
                error=str(e),
                **log_data
            )
            raise