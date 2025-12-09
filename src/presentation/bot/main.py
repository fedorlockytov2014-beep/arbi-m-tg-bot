import asyncio
import logging
from contextlib import asynccontextmanager

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dependency_injector.providers import Singleton
from dependency_injector.containers import DeclarativeContainer

from config.settings import settings
from src.application.use_cases.order_management import AcceptOrderUseCase, SetCookingTimeUseCase, ConfirmReadyUseCase
from src.application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from src.domain.repositories.order_repository import OrderRepository
from src.domain.repositories.warehouse_repository import WarehouseRepository
from src.domain.services.order_service import OrderService
from src.infrastructure.cache.redis_cache import RedisCache
from src.infrastructure.integrations.crm_client import CRMClient
from src.infrastructure.persistence.database import create_engine
from src.infrastructure.persistence.repositories.order_repository_impl import OrderRepositoryImpl
from src.infrastructure.persistence.repositories.warehouse_repository_impl import WarehouseRepositoryImpl
from src.infrastructure.services.order_service_impl import OrderServiceImpl
from src.presentation.bot.dispatcher import get_dispatcher
from src.presentation.bot.handlers.activation_handlers import router as activation_router
from src.presentation.bot.handlers.order_handlers import router as order_router
from src.presentation.bot.middleware.logging_middleware import LoggingMiddleware


# Настройка структурированного логирования
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
        structlog.processors.JSONRenderer() if settings.log_format == "JSON" else structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


class ApplicationContainer(DeclarativeContainer):
    """DI контейнер для приложения"""
    
    # Инфраструктурные зависимости
    database_engine = Singleton(create_engine, settings.database.url)
    redis_cache = Singleton(RedisCache, settings.cache.redis_url)
    crm_client = Singleton(CRMClient)
    
    # Репозитории
    order_repository = Singleton(OrderRepositoryImpl, database_engine, redis_cache)
    warehouse_repository = Singleton(WarehouseRepositoryImpl, database_engine, redis_cache)
    
    # Сервисы
    order_service = Singleton(OrderServiceImpl)
    
    # Use cases
    accept_order_use_case = Singleton(
        AcceptOrderUseCase,
        order_repository,
        warehouse_repository,
        order_service
    )
    set_cooking_time_use_case = Singleton(
        SetCookingTimeUseCase,
        order_repository,
        warehouse_repository,
        order_service
    )
    confirm_ready_use_case = Singleton(
        ConfirmReadyUseCase,
        order_repository,
        warehouse_repository,
        order_service
    )
    activate_warehouse_use_case = Singleton(
        ActivateWarehouseUseCase,
        warehouse_repository
    )


async def setup_bot_commands(bot: Bot):
    """Настраивает команды бота"""
    if settings.bot_menu.enabled:
        from aiogram.types import BotCommand
        commands = [
            BotCommand(command=item["command"], description=item["description"])
            for item in settings.bot_menu.items
        ]
        await bot.set_my_commands(commands)


async def on_startup(bot: Bot, dispatcher: Dispatcher):
    """Действия при запуске бота"""
    logger = structlog.get_logger("bot_startup")
    logger.info("Запуск бота")
    
    # Настраиваем команды бота
    await setup_bot_commands(bot)
    
    logger.info("Бот успешно запущен")


async def on_shutdown(dispatcher: Dispatcher):
    """Действия при выключении бота"""
    logger = structlog.get_logger("bot_shutdown")
    logger.info("Выключение бота")
    
    # Очищаем хранилище состояний
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()
    
    logger.info("Бот успешно выключен")


async def main():
    """Основная функция запуска бота"""
    logger = structlog.get_logger("bot_main")
    logger.info("Инициализация бота")
    
    # Создаем DI контейнер
    container = ApplicationContainer()
    
    # Создаем бота
    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Создаем диспетчер с Redis хранилищем для FSM
    storage = RedisStorage.from_url(settings.cache.redis_url)
    dispatcher = get_dispatcher(storage)
    
    # Регистрируем роутеры
    dispatcher.include_router(activation_router)
    dispatcher.include_router(order_router)
    
    # Передаем use cases в роутеры
    activation_router['activate_warehouse_use_case'] = container.activate_warehouse_use_case()
    order_router['accept_order_use_case'] = container.accept_order_use_case()
    order_router['set_cooking_time_use_case'] = container.set_cooking_time_use_case()
    order_router['confirm_ready_use_case'] = container.confirm_ready_use_case()
    
    # Регистрируем middleware
    dispatcher.message.middleware(LoggingMiddleware())
    dispatcher.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем хуки
    dispatcher.startup.register(lambda dispatcher: on_startup(bot, dispatcher))
    dispatcher.shutdown.register(on_shutdown)
    
    logger.info("Запуск поллинга бота")
    
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    except Exception as e:
        logger.error("Ошибка при запуске бота", error=str(e), exc_info=True)
        raise
    finally:
        await bot.session.close()


def run_webhook():
    """Запуск бота в режиме вебхука"""
    logger = structlog.get_logger("bot_webhook")
    logger.info("Запуск бота в режиме вебхука")
    
    # Создаем DI контейнер
    container = ApplicationContainer()
    
    # Создаем бота
    bot = Bot(
        token=settings.telegram.bot_token,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Создаем диспетчер с Redis хранилищем для FSM
    storage = RedisStorage.from_url(settings.cache.redis_url)
    dispatcher = get_dispatcher(storage)
    
    # Регистрируем роутеры
    dispatcher.include_router(activation_router)
    dispatcher.include_router(order_router)
    
    # Передаем use cases в роутеры
    activation_router['activate_warehouse_use_case'] = container.activate_warehouse_use_case()
    order_router['accept_order_use_case'] = container.accept_order_use_case()
    order_router['set_cooking_time_use_case'] = container.set_cooking_time_use_case()
    order_router['confirm_ready_use_case'] = container.confirm_ready_use_case()
    
    # Регистрируем middleware
    dispatcher.message.middleware(LoggingMiddleware())
    dispatcher.callback_query.middleware(LoggingMiddleware())
    
    # Регистрируем хуки
    dispatcher.startup.register(lambda dispatcher: on_startup(bot, dispatcher))
    dispatcher.shutdown.register(on_shutdown)
    
    # Создаем веб-приложение
    app = web.Application()
    
    # Создаем обработчик запросов
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dispatcher,
        bot=bot
    )
    
    # Регистрируем обработчик на указанный путь
    webhook_requests_handler.register(app, path="/webhook")
    
    # Настраиваем приложение
    setup_application(app, dispatcher, bot=bot)
    
    # Запускаем веб-сервер
    web.run_app(app, host="0.0.0.0", port=settings.telegram.webhook.port)


if __name__ == "__main__":
    if settings.telegram.webhook.enabled:
        run_webhook()
    else:
        asyncio.run(main())