from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


class DIMiddleware(BaseMiddleware):
    """
    Middleware для внедрения зависимостей в обработчики.
    """
    
    def __init__(self, container):
        self.container = container
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Add container to data so handlers can access it
        data['container'] = self.container
        
        # Call the handler with the updated data
        return await handler(event, data)