from aiogram import Dispatcher
from aiogram.types import Message

from ....application.dto.incoming_orders import ActivateWarehouseDTO
from ....application.use_cases.warehouse_activation import ActivateWarehouseUseCase


async def activate_warehouse_command(message: Message, activate_warehouse_use_case: ActivateWarehouseUseCase):
    """
    Обработчик команды активации склада.
    
    Пример: /activate ABC123
    """
    # Получаем аргументы команды
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Использование: /activate <код_активации>")
        return
    
    activation_code = args[1]
    
    # Создаем DTO для активации
    dto = ActivateWarehouseDTO(
        warehouse_uid="default_warehouse",  # В реальном приложении UID будет в сообщении или в другом месте
        activation_code=activation_code,
        chat_id=message.chat.id
    )
    
    try:
        # Выполняем активацию
        success = await activate_warehouse_use_case.execute(dto)
        
        if success:
            await message.reply("Склад успешно активирован!")
        else:
            await message.reply("Не удалось активировать склад. Проверьте код активации.")
            
    except Exception as e:
        await message.reply(f"Ошибка при активации склада: {str(e)}")


def setup_activation_handlers(dp: Dispatcher):
    """
    Настраивает обработчики активации.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(activate_warehouse_command, lambda m: m.text.startswith('/activate'))