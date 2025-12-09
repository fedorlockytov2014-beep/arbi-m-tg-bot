from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ....domain.repositories.warehouse_repository import WarehouseRepository
from ...formatters.order_formatter import format_order_message
from ...keyboards.inline_keyboards import get_order_actions_keyboard


async def help_command(message: Message):
    """
    Обработчик команды /help.
    """
    help_text = (
        "🤖 Помощь по боту склада\n\n"
        "Доступные команды:\n"
        "/start - запустить/перезапустить бота\n"
        "/activate - активировать склад по коду\n"
        "/stats - статистика продаж\n"
        "/orders - посмотреть новые заказы\n"
        "/help - это сообщение\n\n"
        "После активации склада вы будете получать новые заказы "
        "и сможете их обрабатывать через кнопки."
    )
    await message.reply(help_text)


async def orders_command(message: Message, **kwargs):
    """
    Обработчик команды /orders.
    """
    # Получаем контейнер из kwargs
    container = kwargs.get('container')
    if not container:
        await message.reply("Ошибка: контейнер зависимостей не найден.")
        return
    
    # Получаем репозиторий из контейнера
    warehouse_repository: WarehouseRepository = container.warehouse_repository()
    
    # Проверяем, привязан ли чат к складу
    warehouse = await warehouse_repository.get_by_telegram_chat_id(message.chat.id)
    
    if not warehouse:
        await message.reply("Сначала активируйте склад. Используйте команду /start и перейдите по ссылке активации.")
        return
    
    # В реальном приложении здесь нужно получить новые заказы для склада
    # Пока покажем заглушку
    await message.reply("Новых заказов пока нет. Как только они поступят, они появятся здесь.")


def setup_common_handlers(dp: Dispatcher):
    """
    Настраивает общие обработчики.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(help_command, lambda m: m.text.startswith('/help'))
    dp.message.register(orders_command, lambda m: m.text.startswith('/orders'))