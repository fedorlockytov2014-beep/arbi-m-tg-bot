from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ....application.dto.incoming_orders import ActivateWarehouseDTO
from ....application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from ...keyboards.inline_keyboards import get_order_actions_keyboard
from ..states import WarehouseActivation


async def start_command(
    message: Message, 
    warehouse_repository,
    activate_warehouse_use_case: ActivateWarehouseUseCase
):
    """
    Обработчик команды /start.
    """
    # Проверяем, есть ли в сообщении start_payload (для deep-link)
    if hasattr(message, 'text') and ' ' in message.text:
        args = message.text.split(' ', 1)
        if len(args) > 1:
            warehouse_uid = args[1]
            
            # Пытаемся активировать склад по UID
            dto = ActivateWarehouseDTO(
                warehouse_uid=warehouse_uid,
                activation_code="",  # Для deep-link активации код не нужен
                chat_id=message.chat.id
            )
            
            try:
                # Выполняем активацию
                success = await activate_warehouse_use_case.execute(dto)
                
                if success:
                    # Получаем информацию о складе
                    warehouse = await warehouse_repository.get_by_uid(warehouse_uid)
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


async def process_activation_code(
    message: Message, 
    activate_warehouse_use_case: ActivateWarehouseUseCase,
    state: FSMContext
):
    """
    Обработчик ввода кода активации.
    """
    activation_code = message.text.strip()
    
    # В реальном приложении нужно будет найти warehouse_uid по коду активации
    # или использовать дополнительный сервис для поиска
    # Пока используем упрощенную логику - нужно получить warehouse_uid по коду
    
    # В реальности нужно использовать метод репозитория для поиска по коду
    # warehouse = await warehouse_repository.find_by_activation_code(activation_code)
    # if warehouse:
    #     warehouse_uid = warehouse.uid
    # else:
    #     await message.reply("Неверный код активации. Проверьте код или обратитесь к администратору.")
    #     return
    
    # Для демонстрации используем фиктивный UID
    # В реальном приложении нужно будет реализовать поиск склада по коду активации
    await message.reply("Функционал активации по коду в разработке. Пожалуйста, используйте deep-link активацию.")
    await state.clear()


async def activate_warehouse_by_code_command(
    message: Message, 
    activate_warehouse_use_case: ActivateWarehouseUseCase
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
    
    # В реальной реализации нужно сначала найти warehouse_uid по коду активации
    # Для этого нужно использовать дополнительный метод репозитория или сервис
    # Пока покажем сообщение о том, что функция в разработке
    await message.reply("Функционал активации по коду в разработке. Пожалуйста, используйте deep-link активацию.")


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