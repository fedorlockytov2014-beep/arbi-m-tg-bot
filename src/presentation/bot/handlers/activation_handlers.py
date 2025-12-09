import logging
from typing import Optional

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from src.presentation.bot.states import WarehouseActivation
from src.presentation.keyboards.inline_keyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(lambda m: m.text and m.text.lower() == 'активировать склад')
@router.message(lambda m: m.text and m.text.lower() == '/activate')
async def activate_warehouse_command(
    message: Message,
    state: FSMContext
):
    """
    Обработка команды активации склада.
    """
    logger.info(
        "Пользователь запросил активацию склада",
        chat_id=message.chat.id
    )
    
    # Проверяем, не активирован ли уже склад для этого чата
    # (предполагаем, что у нас есть способ проверки через use case)
    
    await message.answer(
        "Введите код активации склада:"
    )
    
    # Переход в состояние ожидания кода активации
    await state.set_state(WarehouseActivation.waiting_for_activation_code)


@router.message(WarehouseActivation.waiting_for_activation_code)
async def process_activation_code(
    message: Message,
    activate_warehouse_use_case: ActivateWarehouseUseCase,
    state: FSMContext
):
    """
    Обработка ввода кода активации.
    """
    activation_code = message.text.strip()
    
    logger.info(
        "Получен код активации",
        chat_id=message.chat.id,
        activation_code=activation_code
    )
    
    try:
        # Подготовка DTO
        dto = activate_warehouse_use_case.ActivateWarehouseDTO(
            chat_id=message.chat.id,
            activation_code=activation_code
        )
        
        # Выполнение активации
        warehouse = await activate_warehouse_use_case.execute(dto)
        
        await message.answer(
            f"✅ Магазин <b>{warehouse.name}</b> успешно привязан к чату!",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Сброс состояния
        await state.clear()
        
        logger.info(
            "Склад успешно активирован",
            chat_id=message.chat.id,
            warehouse_id=warehouse.uid
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при активации склада",
            chat_id=message.chat.id,
            activation_code=activation_code,
            error=str(e),
            exc_info=True
        )
        await message.answer(
            "❌ Неверный код или склад уже привязан. Попробуйте ещё раз."
        )


@router.message(lambda m: m.text and m.text.lower() == '/start')
async def start_command(
    message: Message,
    activate_warehouse_use_case: ActivateWarehouseUseCase,
    state: FSMContext
):
    """
    Обработка команды /start.
    """
    chat_id = message.chat.id
    
    logger.info(
        "Пользователь запустил бота",
        chat_id=chat_id
    )
    
    # Проверяем, есть ли параметры в команде (deep-linking)
    start_param = None
    if len(message.text.split()) > 1:
        start_param = message.text.split()[1]
    
    if start_param:
        # Обработка deep-link с UID склада
        try:
            # Подготовка DTO
            dto = activate_warehouse_use_case.ActivateWarehouseByUidDTO(
                chat_id=chat_id,
                warehouse_uid=start_param
            )
            
            # Выполнение активации по UID
            warehouse = await activate_warehouse_use_case.execute_by_uid(dto)
            
            await message.answer(
                f"✅ Магазин <b>{warehouse.name}</b> успешно привязан к чату!",
                reply_markup=get_main_menu_keyboard()
            )
            
            logger.info(
                "Склад успешно привязан через deep-link",
                chat_id=chat_id,
                warehouse_id=warehouse.uid
            )
            
        except Exception as e:
            logger.error(
                "Ошибка при привязке склада через deep-link",
                chat_id=chat_id,
                warehouse_uid=start_param,
                error=str(e),
                exc_info=True
            )
            await message.answer(
                "❌ Неверный код или склад уже привязан. Попробуйте активировать вручную."
            )
    else:
        # Проверяем, активирован ли уже склад для этого чата
        is_activated = await activate_warehouse_use_case.is_chat_activated(chat_id)
        
        if is_activated:
            await message.answer(
                "🏠 Добро пожаловать! Выберите действие:",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "Привет! Я бот для приёма заказов. "
                "Чтобы начать работу, активируйте склад.\n\n"
                "Нажмите кнопку ниже или введите команду /activate:",
                reply_markup=types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="🔐 Активировать склад",
                                callback_data="activate_warehouse"
                            )
                        ]
                    ]
                )
            )