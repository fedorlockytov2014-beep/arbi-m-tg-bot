from aiogram import Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from .handlers.activation_handlers import setup_activation_handlers
from .handlers.order_handlers import setup_order_handlers
from .handlers.statistics_handlers import setup_statistics_handlers
from .handlers.common_handlers import setup_common_handlers


def get_dispatcher(storage: RedisStorage) -> Dispatcher:
    """
    Создает и настраивает диспетчер.
    
    Args:
        storage: Хранилище состояний FSM
        
    Returns:
        Dispatcher: Настроенный диспетчер
    """
    # Создание диспетчера с указанным хранилищем
    dp = Dispatcher(storage=storage)
    
    # Настройка обработчиков
    setup_activation_handlers(dp)
    setup_order_handlers(dp)
    setup_statistics_handlers(dp)
    setup_common_handlers(dp)
    
    return dp