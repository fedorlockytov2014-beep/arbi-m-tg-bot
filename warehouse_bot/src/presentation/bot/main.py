import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage

from warehouse_bot.config.settings import settings
from warehouse_bot.src.infrastructure.di.container import Container
from warehouse_bot.src.infrastructure.logging.config import setup_logging
from warehouse_bot.src.presentation.bot.dispatcher import get_dispatcher
from warehouse_bot.src.presentation.bot.middleware.di_middleware import DIMiddleware



logger = logging.getLogger(__name__)


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
    Инициализация при запуске бота.
    """
    # Инициализация DI контейнера
    container = Container()
    container.config.from_dict(settings.model_dump())

    # Подключаем DI к нужным модулям
    # Замените "presentation" на реальный путь к вашим хендлерам
    container.wire(packages=["warehouse_bot.src.presentation"])

    # Сохраняем контейнер в диспетчере (опционально, если используете middleware)
    dispatcher.container = container

    # Регистрируем middleware (если вы НЕ используете @inject)
    dispatcher.message.middleware(DIMiddleware(container))
    dispatcher.callback_query.middleware(DIMiddleware(container))

    logger.info("DI контейнер инициализирован. Бот запускается...")


async def on_shutdown(dispatcher: Dispatcher):
    """
    Очистка при остановке бота.
    """
    container = getattr(dispatcher, "container", None)
    if container:
        await container.shutdown_resources()  # если есть асинхронные ресурсы
        container.unwire()  # отключаем DI

    logger.info("Бот остановлен. Ресурсы освобождены.")


if __name__ == "__main__":

    asyncio.run(main())