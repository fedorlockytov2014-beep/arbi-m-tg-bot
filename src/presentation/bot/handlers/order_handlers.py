import logging
from datetime import datetime, timedelta
from typing import cast

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from src.application.dto.incoming_orders import AcceptOrderDTO, SetCookingTimeDTO, ConfirmReadyDTO
from src.application.use_cases.order_management import AcceptOrderUseCase, SetCookingTimeUseCase, ConfirmReadyUseCase
from src.domain.value_objects.order_status import OrderStatus
from src.presentation.bot.states import OrderProcessing
from src.presentation.formatters.order_formatter import format_cooking_time_confirmation, format_order_ready_confirmation
from src.presentation.keyboards.inline_keyboards import get_cooking_time_keyboard, get_confirm_ready_keyboard

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(lambda c: c.data.startswith('accept_order_'))
async def process_accept_order_callback(
    callback_query: CallbackQuery,
    accept_order_use_case: AcceptOrderUseCase,
    state: FSMContext
):
    """
    Обработка нажатия кнопки 'Взять заказ'.
    Проверяет, свободен ли заказ, и если да - меняет статус на 'accepted_by_partner'.
    """
    order_id = callback_query.data.split('_')[2]
    
    logger.info(
        "Партнёр пытается принять заказ",
        order_id=order_id,
        chat_id=callback_query.message.chat.id
    )
    
    try:
        # Подготовка данных для use case
        dto = AcceptOrderDTO(
            order_id=order_id,
            chat_id=callback_query.message.chat.id,
            warehouse_uid=""  # будет заполнен в use case
        )
        
        # Выполнение принятия заказа
        order = await accept_order_use_case.execute(dto)
        
        # Редактирование сообщения
        await callback_query.message.edit_text(
            text=f"✅ Заказ #{order_id} принят. Укажите время готовности:",
            reply_markup=get_cooking_time_keyboard()
        )
        
        # Сохранение order_id в состоянии для дальнейшей обработки
        await state.update_data(current_order_id=order_id)
        
        # Переход в состояние ожидания времени готовки
        await state.set_state(OrderProcessing.waiting_for_cooking_time)
        
        await callback_query.answer("Заказ принят. Укажите время готовности.")
        
        logger.info(
            "Заказ успешно принят партнёром",
            order_id=order_id,
            chat_id=callback_query.message.chat.id
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при принятии заказа",
            order_id=order_id,
            chat_id=callback_query.message.chat.id,
            error=str(e),
            exc_info=True
        )
        await callback_query.answer(
            "Не удалось принять заказ. Возможно, он уже занят другим партнёром.",
            show_alert=True
        )


@router.callback_query(lambda c: c.data.startswith('cooking_time_'))
async def process_cooking_time_callback(
    callback_query: CallbackQuery,
    set_cooking_time_use_case: SetCookingTimeUseCase,
    state: FSMContext
):
    """
    Обработка выбора времени готовки через кнопки.
    """
    cooking_time = int(callback_query.data.split('_')[2])
    
    # Получение order_id из состояния
    data = await state.get_data()
    order_id = data.get('current_order_id')
    
    if not order_id:
        await callback_query.answer("Ошибка: заказ не найден в состоянии.", show_alert=True)
        return
    
    logger.info(
        "Партнёр выбрал время готовки",
        order_id=order_id,
        cooking_time=cooking_time,
        chat_id=callback_query.message.chat.id
    )
    
    try:
        # Подготовка DTO
        dto = SetCookingTimeDTO(
            order_id=order_id,
            chat_id=callback_query.message.chat.id,
            cooking_time_minutes=cooking_time
        )
        
        # Выполнение установки времени готовки
        order = await set_cooking_time_use_case.execute(dto)
        
        # Форматирование времени готовности
        expected_ready_at = (datetime.utcnow() + timedelta(minutes=cooking_time)).strftime('%H:%M')
        
        # Редактирование сообщения
        await callback_query.message.edit_text(
            text=format_cooking_time_confirmation(cooking_time, expected_ready_at),
            reply_markup=get_confirm_ready_keyboard(order_id)
        )
        
        await callback_query.answer(f"Время готовки: {cooking_time} мин")
        
        logger.info(
            "Время готовки установлено",
            order_id=order_id,
            cooking_time=cooking_time
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при установке времени готовки",
            order_id=order_id,
            cooking_time=cooking_time,
            error=str(e),
            exc_info=True
        )
        await callback_query.answer(
            "Не удалось установить время готовки. Попробуйте ещё раз.",
            show_alert=True
        )


@router.message(OrderProcessing.waiting_for_cooking_time)
async def process_cooking_time_text(
    message: Message,
    set_cooking_time_use_case: SetCookingTimeUseCase,
    state: FSMContext
):
    """
    Обработка ввода времени готовки в виде текста.
    """
    try:
        cooking_time = int(message.text.strip())
        
        # Проверка диапазона
        if cooking_time < 1 or cooking_time > 180:
            await message.reply("⏱ Пожалуйста, укажите время в минутах (1–180)")
            return
        
        # Получение order_id из состояния
        data = await state.get_data()
        order_id = data.get('current_order_id')
        
        if not order_id:
            await message.reply("❌ Ошибка: заказ не найден в состоянии.")
            return
        
        logger.info(
            "Партнёр ввёл время готовки",
            order_id=order_id,
            cooking_time=cooking_time,
            chat_id=message.chat.id
        )
        
        # Подготовка DTO
        dto = SetCookingTimeDTO(
            order_id=order_id,
            chat_id=message.chat.id,
            cooking_time_minutes=cooking_time
        )
        
        # Выполнение установки времени готовки
        order = await set_cooking_time_use_case.execute(dto)
        
        # Форматирование времени готовности
        expected_ready_at = (datetime.utcnow() + timedelta(minutes=cooking_time)).strftime('%H:%M')
        
        # Отправка сообщения
        await message.answer(
            text=format_cooking_time_confirmation(cooking_time, expected_ready_at),
            reply_markup=get_confirm_ready_keyboard(order_id)
        )
        
        logger.info(
            "Время готовки установлено через текст",
            order_id=order_id,
            cooking_time=cooking_time
        )
        
    except ValueError:
        await message.reply("🔢 Пожалуйста, введите целое число минут (например, 25)")
    except Exception as e:
        logger.error(
            "Ошибка при установке времени готовки через текст",
            chat_id=message.chat.id,
            error=str(e),
            exc_info=True
        )
        await message.reply("❌ Не удалось установить время готовки. Попробуйте ещё раз.")


@router.callback_query(lambda c: c.data.startswith('order_ready_'))
async def process_order_ready_callback(
    callback_query: CallbackQuery,
    state: FSMContext
):
    """
    Обработка нажатия кнопки 'Заказ готов'.
    Переходит в состояние ожидания фото.
    """
    order_id = callback_query.data.split('_')[2]
    
    logger.info(
        "Партнёр отметил заказ как готовый",
        order_id=order_id,
        chat_id=callback_query.message.chat.id
    )
    
    # Сохранение order_id в состоянии
    await state.update_data(current_order_id=order_id)
    
    # Переход в состояние ожидания фото
    await state.set_state(OrderProcessing.waiting_for_photos)
    
    await callback_query.message.edit_text(
        text=f"📸 Отправьте фото собранного заказа #{order_id}"
    )
    
    await callback_query.answer("Отправьте фото заказа")


@router.message(OrderProcessing.waiting_for_photos, ~types.ContentType.PHOTO)
async def process_non_photo_in_photos_state(message: Message):
    """
    Обработка отправки не-фото в состоянии ожидания фото.
    """
    await message.reply("📸 Пожалуйста, отправьте именно фотографию заказа.")


@router.message(OrderProcessing.waiting_for_photos, types.ContentType.PHOTO)
async def process_photo_in_photos_state(message: Message, state: FSMContext):
    """
    Обработка отправки фото в состоянии ожидания фото.
    """
    # Получение order_id из состояния
    data = await state.get_data()
    order_id = data.get('current_order_id')
    
    if not order_id:
        await message.reply("❌ Ошибка: заказ не найден в состоянии.")
        return
    
    # Получение file_id фото
    photo = message.photo[-1]  # Берём фото в лучшем качестве
    file_id = photo.file_id
    
    # Получение сохранённых фото из состояния
    photos_data = data.get('order_photos', [])
    
    # Проверка ограничения на количество фото
    if len(photos_data) >= 3:
        await message.reply("🖼 Достигнуто максимальное количество фото (3).")
        return
    
    # Добавление нового фото
    photos_data.append(file_id)
    
    # Обновление состояния
    await state.update_data(order_photos=photos_data)
    
    await message.reply(
        text=f"✅ Фото добавлено ({len(photos_data)}/3).",
        reply_markup=get_confirm_ready_keyboard(order_id)
    )


@router.callback_query(lambda c: c.data.startswith('confirm_ready_'), OrderProcessing.waiting_for_photos)
async def process_confirm_ready_callback(
    callback_query: CallbackQuery,
    confirm_ready_use_case: ConfirmReadyUseCase,
    state: FSMContext
):
    """
    Обработка подтверждения готовности заказа с фото.
    """
    order_id = callback_query.data.split('_')[2]
    
    logger.info(
        "Партнёр подтверждает готовность заказа",
        order_id=order_id,
        chat_id=callback_query.message.chat.id
    )
    
    # Получение фото из состояния
    data = await state.get_data()
    photos = data.get('order_photos', [])
    
    try:
        # Подготовка DTO
        dto = ConfirmReadyDTO(
            order_id=order_id,
            chat_id=callback_query.message.chat.id,
            photo_file_ids=photos
        )
        
        # Выполнение подтверждения готовности
        order = await confirm_ready_use_case.execute(dto)
        
        # Отправка сообщения о готовности
        await callback_query.message.edit_text(
            text=format_order_ready_confirmation(order_id)
        )
        
        # Сброс состояния для этого заказа
        await state.clear()
        
        await callback_query.answer("Заказ готов к доставке!")
        
        logger.info(
            "Готовность заказа подтверждена",
            order_id=order_id
        )
        
    except Exception as e:
        logger.error(
            "Ошибка при подтверждении готовности заказа",
            order_id=order_id,
            error=str(e),
            exc_info=True
        )
        await callback_query.answer(
            "❌ Не удалось подтвердить готовность. Повторите действие.",
            show_alert=True
        )