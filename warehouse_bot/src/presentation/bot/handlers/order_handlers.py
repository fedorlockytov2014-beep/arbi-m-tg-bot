from aiogram import Dispatcher
from aiogram.types import Message

from ....application.dto.incoming_orders import AcceptOrderDTO, SetCookingTimeDTO
from ....application.use_cases.order_management import AcceptOrderUseCase, SetCookingTimeUseCase


async def accept_order_command(message: Message, accept_order_use_case: AcceptOrderUseCase):
    """
    Обработчик команды принятия заказа.
    
    Пример: /accept_order ORDER123
    """
    # Получаем аргументы команды
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Использование: /accept_order <ID_заказа>")
        return
    
    order_id = args[1]
    
    # В реальном приложении warehouse_uid должен приходить из контекста (например, из состояния FSM или из базы)
    # Здесь используем заглушку
    dto = AcceptOrderDTO(
        order_id=order_id,
        warehouse_uid="default_warehouse",  # В реальном приложении будет определен из контекста
        chat_id=message.chat.id
    )
    
    try:
        # Выполняем принятие заказа
        order = await accept_order_use_case.execute(dto)
        
        await message.reply(f"Заказ {order_id} успешно принят! Время принятия: {order.accepted_at}")
        
    except Exception as e:
        await message.reply(f"Ошибка при принятии заказа: {str(e)}")


async def set_cooking_time_command(message: Message, set_cooking_time_use_case: SetCookingTimeUseCase):
    """
    Обработчик команды установки времени приготовления.
    
    Пример: /set_cooking_time ORDER123 45
    """
    # Получаем аргументы команды
    args = message.text.split()
    if len(args) != 3:
        await message.reply("Использование: /set_cooking_time <ID_заказа> <время_в_минутах>")
        return
    
    order_id = args[1]
    try:
        cooking_time_minutes = int(args[2])
    except ValueError:
        await message.reply("Время приготовления должно быть числом")
        return
    
    # Создаем DTO для установки времени приготовления
    dto = SetCookingTimeDTO(
        order_id=order_id,
        warehouse_uid="default_warehouse",  # В реальном приложении будет определен из контекста
        chat_id=message.chat.id,
        cooking_time_minutes=cooking_time_minutes
    )
    
    try:
        # Выполняем установку времени приготовления
        order = await set_cooking_time_use_case.execute(dto)
        
        await message.reply(
            f"Время приготовления для заказа {order_id} установлено: {order.cooking_time_minutes} минут. "
            f"Ожидаемое время готовности: {order.expected_ready_at}"
        )
        
    except Exception as e:
        await message.reply(f"Ошибка при установке времени приготовления: {str(e)}")


def setup_order_handlers(dp: Dispatcher):
    """
    Настраивает обработчики заказов.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(accept_order_command, lambda m: m.text.startswith('/accept_order'))
    dp.message.register(set_cooking_time_command, lambda m: m.text.startswith('/set_cooking_time'))