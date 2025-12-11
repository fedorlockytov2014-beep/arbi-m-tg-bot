from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from ....application.dto.incoming_orders import ActivateWarehouseDTO
from ....application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from ....domain.repositories.warehouse_repository import WarehouseRepository
from ...keyboards.inline_keyboards import get_order_actions_keyboard
from ..states import WarehouseActivation
from ....infrastructure.di.container import Container


@inject
async def start_command(
    message: Message,
    activate_warehouse_use_case: ActivateWarehouseUseCase = Provide[Container.activate_warehouse_use_case],
    warehouse_repository: WarehouseRepository = Provide[Container.warehouse_repository]
):
    """
    Обработчик команды /start.
    """
    # Проверяем, есть ли в сообщении start_payload (для deep-link)
    if hasattr(message, 'text') and ' ' in message.text:
        args = message.text.split(' ', 1)
        if len(args) > 1:
            warehouse_id = args[1]
            
            # Пытаемся активировать склад по UID
            dto = ActivateWarehouseDTO(
                warehouse_id=warehouse_id,
                activation_code="",  # Для deep-link активации код не нужен
                chat_id=message.chat.id
            )
            
            try:
                # Выполняем активацию
                success = await activate_warehouse_use_case.execute(dto)
                
                if success:
                    # Получаем информацию о складе
                    warehouse = await warehouse_repository.get_by_id(warehouse_id)
                    if warehouse:
                        await message.reply(f"Магазин {warehouse.name} успешно привязан к этому чату!")
                    else:
                        await message.reply("Склад успешно привязан к этому чату!")
                else:
                    await message.reply("Не удалось активировать склад. Проверьте данные или обратитесь к администратору.")
                    
            except Exception as e:
                await message.reply(f"Ошибка при активации склада: {str(e)}")
            return
    
    # Если нет deep-link, проверяем, привязан ли уже чат к складу
    warehouse = await warehouse_repository.get_by_telegram_chat_id(message.chat.id)
    
    if warehouse:
        await message.reply(
            f"Привет! Вы уже подключены к складу {warehouse.name}.\n"
            f"Доступные команды:\n"
            f"/orders - посмотреть новые заказы\n"
            f"/stats - статистика продаж"
        )
    else:
        await message.reply(
            "Привет! Я бот для приёма заказов.\n"
            "Для активации вашего магазина используйте уникальную ссылку или код, выданный вам в админ-панели.\n\n"
            "Используйте команду /activate для ручной активации."
        )


async def activate_command(message: Message, state: FSMContext):
    """
    Обработчик команды /activate.
    """
    await message.reply("Пожалуйста, введите код активации:")
    await state.set_state(WarehouseActivation.waiting_for_activation_code)


@inject
async def process_activation_code(
    message: Message, 
    state: FSMContext,
    activate_warehouse_use_case: ActivateWarehouseUseCase = Provide[Container.activate_warehouse_use_case],
    warehouse_repository: WarehouseRepository = Provide[Container.warehouse_repository]
):
    """
    Обработчик ввода кода активации.
    """
    activation_code = message.text.strip()
    
    # Ищем склад по коду активации
    warehouse = await warehouse_repository.find_by_activation_code(activation_code)
    if not warehouse:
        await message.reply("Неверный код активации. Проверьте код или обратитесь к администратору.")
        await state.clear()
        return
    
    # Активируем склад
    dto = ActivateWarehouseDTO(
        warehouse_id=warehouse.id,
        activation_code=activation_code,
        chat_id=message.chat.id
    )
    
    try:
        success = await activate_warehouse_use_case.execute(dto)
        
        if success:
            await message.reply(f"Магазин {warehouse.name} успешно привязан к этому чату!")
        else:
            await message.reply("Не удалось активировать склад. Проверьте данные или обратитесь к администратору.")
    except Exception as e:
        await message.reply(f"Ошибка при активации склада: {str(e)}")
    
    await state.clear()


@inject
async def activate_warehouse_by_code_command(
    message: Message,
    activate_warehouse_use_case: ActivateWarehouseUseCase = Provide[Container.activate_warehouse_use_case],
    warehouse_repository: WarehouseRepository = Provide[Container.warehouse_repository]
):
    """
    Обработчик команды активации склада по коду.
    
    Пример: /activate ABC123
    """
    # Получаем аргументы команды
    args = message.text.split()
    if len(args) != 2:
        await message.reply("Использование: /activate <код_активации>")
        return
    
    activation_code = args[1]
    
    # Ищем склад по коду активации
    warehouse = await warehouse_repository.find_by_activation_code(activation_code)
    if not warehouse:
        await message.reply("Неверный код активации. Проверьте код или обратитесь к администратору.")
        return
    
    # Активируем склад
    dto = ActivateWarehouseDTO(
        warehouse_id=warehouse.id,
        activation_code=activation_code,
        chat_id=message.chat.id
    )
    
    try:
        success = await activate_warehouse_use_case.execute(dto)
        
        if success:
            await message.reply(f"Магазин {warehouse.name} успешно привязан к этому чату!")
        else:
            await message.reply("Не удалось активировать склад. Проверьте данные или обратитесь к администратору.")
    except Exception as e:
        await message.reply(f"Ошибка при активации склада: {str(e)}")


def setup_activation_handlers(dp: Dispatcher):
    """
    Настраивает обработчики активации.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(start_command, lambda m: m.text.startswith('/start'))
    dp.message.register(activate_command, lambda m: m.text.startswith('/activate'))
    dp.message.register(process_activation_code, WarehouseActivation.waiting_for_activation_code)
    dp.message.register(activate_warehouse_by_code_command, lambda m: m.text.startswith('/activate '))
