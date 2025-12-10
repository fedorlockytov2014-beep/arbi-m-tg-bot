from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from ....domain.repositories.warehouse_repository import WarehouseRepository
from ....domain.repositories.order_repository import OrderRepository
from ....domain.value_objects.order_status import OrderStatus
from ...formatters.order_formatter import format_order_message
from ...keyboards.inline_keyboards import get_order_actions_keyboard
from ....infrastructure.logging import get_logger, log_user_action, log_server_action, log_error

logger = get_logger(__name__)


async def help_command(message: Message):
    """
    Обработчик команды /help.
    """
    await log_user_action(
        logger,
        user_id=message.from_user.id,
        action="help_command",
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    
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
    
    await log_server_action(
        logger,
        action="help_response_sent",
        result="success",
        user_id=message.from_user.id,
        chat_id=message.chat.id
    )


@inject
async def orders_command(
    message: Message,
    warehouse_repository: WarehouseRepository = Provide["warehouse_repository"],
    order_repository: OrderRepository = Provide["order_repository"]
):
    """
    Обработчик команды /orders.
    """
    await log_user_action(
        logger,
        user_id=message.from_user.id,
        action="orders_command",
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    
    try:
        # Проверяем, привязан ли чат к складу
        warehouse = await warehouse_repository.get_by_telegram_chat_id(message.chat.id)
        
        if not warehouse:
            response_text = "Сначала активируйте склад. Используйте команду /start и перейдите по ссылке активации."
            await message.reply(response_text)
            
            await log_server_action(
                logger,
                action="warehouse_not_found_for_chat",
                result="warning",
                user_id=message.from_user.id,
                chat_id=message.chat.id
            )
            return
        
        # Получаем новые заказы для склада (с определенными статусами)
        # В соответствии с ТЗ, показываем заказы с определенными статусами
        new_orders = await order_repository.get_by_warehouse_and_status(
            warehouse_id=str(warehouse.id),
            status=OrderStatus.NEW  # или другие статусы для новых заказов
        )
        
        if not new_orders:
            response_text = "Новых заказов пока нет. Как только они поступят, они появятся здесь."
            await message.reply(response_text)
        else:
            # Отправляем информацию о каждом заказе
            for order in new_orders:
                order_message = format_order_message(order)
                await message.reply(
                    order_message,
                    reply_markup=get_order_actions_keyboard(order.id)
                )
        
        await log_server_action(
            logger,
            action="orders_response_sent",
            result="success",
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            warehouse_uid=warehouse.uid,
            orders_count=len(new_orders)
        )
        
    except Exception as e:
        await log_error(
            logger,
            e,
            context={
                "user_id": message.from_user.id,
                "chat_id": message.chat.id,
                "command": "/orders"
            }
        )
        await message.reply("Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.")


def setup_common_handlers(dp: Dispatcher):
    """
    Настраивает общие обработчики.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(help_command, lambda m: m.text.startswith('/help'))
    dp.message.register(orders_command, lambda m: m.text.startswith('/orders'))