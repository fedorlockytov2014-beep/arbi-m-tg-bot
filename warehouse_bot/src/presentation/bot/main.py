import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage

from ...config.settings import settings
from ...infrastructure.di.container import Container
from .dispatcher import get_dispatcher
from ...infrastructure.logging.config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(dp: Dispatcher):
    """
    Управляет жизненным циклом приложения.
    """
    # Инициализация DI контейнера
    container = Container()
    container.wire(modules=[sys.modules[__name__]])
    
    # Передаем контейнер в диспетчер
    dp.container = container
    
    logger.info("Бот запускается...")
    yield
    logger.info("Бот останавливается...")


async def main():
    """
    Основная точка входа бота.
    """
    # Настройка логирования
    setup_logging()
    
    # Создание сессии для бота
    session = AiohttpSession()
    
    # Создание бота
    bot = Bot(
        token=settings.telegram.bot_token,
        session=session
    )
    
    # Создание хранилища состояний FSM в Redis
    storage = RedisStorage.from_url(settings.cache.redis_url)
    
    # Получение диспетчера
    dp = get_dispatcher(storage)
    
    # Установка жизненного цикла
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        # Запуск бота в режиме long polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


async def on_startup(dispatcher: Dispatcher):
    """
    Вызывается при запуске бота.
    """
    logger.info("Бот запущен и готов к работе")


async def on_shutdown(dispatcher: Dispatcher):
    """
    Вызывается при остановке бота.
    """
    logger.info("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())