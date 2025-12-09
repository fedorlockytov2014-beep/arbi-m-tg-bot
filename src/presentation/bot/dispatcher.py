from aiogram import Dispatcher
from aiogram.fsm.storage.base import BaseStorage


def get_dispatcher(storage: BaseStorage) -> Dispatcher:
    """
    Создает и возвращает диспетчер с настройками.
    
    Args:
        storage: Хранилище состояний FSM
        
    Returns:
        Dispatcher: Настроенный диспетчер
    """
    # Создаем диспетчер с указанным хранилищем
    dispatcher = Dispatcher(storage=storage)
    
    # Настраиваем диспетчер
    dispatcher["bot"] = None  # будет установлен позже
    
    return dispatcher