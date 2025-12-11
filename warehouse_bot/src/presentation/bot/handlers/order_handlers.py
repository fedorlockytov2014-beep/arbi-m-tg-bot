from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from dependency_injector.wiring import Provide, inject

from ....application.dto.incoming_orders import AcceptOrderDTO, SetCookingTimeDTO, AddOrderPhotoDTO, CancelOrderDTO
from ....application.use_cases.order_management import AcceptOrderUseCase, SetCookingTimeUseCase, CancelOrderUseCase
from ....domain.repositories.warehouse_repository import IWarehouseRepository
from ...formatters.order_formatter import format_order_message, format_order_status_message
from ...keyboards.inline_keyboards import get_order_actions_keyboard, get_cooking_time_keyboard, get_ready_for_delivery_keyboard, get_confirm_ready_keyboard
from ..states import OrderProcessing


@inject
async def handle_new_order_callback(
    callback: CallbackQuery,
    accept_order_use_case: AcceptOrderUseCase = Provide["accept_order_use_case"],
    warehouse_repository: IWarehouseRepository = Provide["warehouse_repository"]
):
    """
    Обработчик нажатия кнопки 'Взять заказ'.
    """
    order_id = callback.data.split('_')[2]  # accept_order_{order_id}
    
    # Получаем склад по chat_id
    warehouse = await warehouse_repository.get_by_telegram_chat_id(callback.message.chat.id)
    if not warehouse:
        await callback.answer("Склад не найден. Сначала активируйте склад.", show_alert=True)
        return
    
    dto = AcceptOrderDTO(
        order_id=order_id,
        warehouse_id=warehouse.id,
        chat_id=callback.message.chat.id
    )
    
    try:
        order = await accept_order_use_case.execute(dto)
        await callback.message.edit_text(
            text=f"Заказ {order_id} принят!\nТеперь укажите время готовности (в минутах):",
            reply_markup=get_cooking_time_keyboard()
        )
        await callback.answer("Заказ принят")
    except Exception as e:
        await callback.answer(f"Ошибка при принятии заказа: {str(e)}", show_alert=True)


@inject
async def handle_cancel_order_callback(
    callback: CallbackQuery,
    cancel_order_use_case: CancelOrderUseCase = Provide["cancel_order_use_case"],
    warehouse_repository: IWarehouseRepository = Provide["warehouse_repository"]
):
    """
    Обработчик нажатия кнопки 'Отменить заказ'.
    """
    order_id = callback.data.split('_')[2]  # cancel_order_{order_id}
    
    # Получаем склад по chat_id
    warehouse = await warehouse_repository.get_by_telegram_chat_id(callback.message.chat.id)
    if not warehouse:
        await callback.answer("Склад не найден. Сначала активируйте склад.", show_alert=True)
        return
    
    dto = CancelOrderDTO(
        order_id=order_id,
        warehouse_id=warehouse.id,
        chat_id=callback.message.chat.id
    )
    
    try:
        order = await cancel_order_use_case.execute(dto)
        await callback.message.edit_text(
            text=f"Заказ {order_id} отменен!"
        )
        await callback.answer("Заказ отменен")
    except Exception as e:
        await callback.answer(f"Ошибка при отмене заказа: {str(e)}", show_alert=True)


async def handle_cooking_time_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Обработчик выбора времени готовки.
    """
    cooking_time = int(callback.data.split('_')[2])  # cooking_time_{minutes}
    
    # Сохраняем время готовки в состоянии
    await state.update_data(cooking_time_minutes=cooking_time)
    
    await callback.message.edit_text(
        f"Время готовности: {cooking_time} минут.\n"
        f"Ожидаемое время готовности: {cooking_time} мин с момента приготовления.\n\n"
        f"Теперь нажмите кнопку 'Заказ готов', когда он будет собран."
    )
    
    # Добавляем кнопку "Заказ готов"
    order_id = callback.data.split('_')[2]  # Need to get order_id differently
    # For now, we'll assume we have the order_id from state
    state_data = await state.get_data()
    current_order_id = state_data.get('current_order_id', 'unknown')
    
    await callback.message.edit_reply_markup(
        reply_markup=get_ready_for_delivery_keyboard(current_order_id)
    )
    
    await callback.answer("Время готовности установлено")


async def handle_ready_for_delivery_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Обработчик нажатия кнопки 'Заказ готов'.
    """
    order_id = callback.data.split('_')[3]  # ready_for_delivery_{order_id}
    
    await state.update_data(current_order_id=order_id)
    
    await callback.message.edit_text(
        "Отправьте, пожалуйста, фото собранного заказа (можно несколько).\n"
        "После отправки нажмите кнопку 'Подтвердить готовность'."
    )
    
    # Добавляем кнопку подтверждения готовности
    await callback.message.edit_reply_markup(
        reply_markup=get_confirm_ready_keyboard(order_id)
    )
    
    # Переходим в состояние ожидания фото
    await state.set_state(OrderProcessing.waiting_for_photos)
    
    await callback.answer("Отправьте фото заказа")


async def handle_photo_upload(message: Message, state: FSMContext):
    """
    Обработчик загрузки фото.
    """
    state_data = await state.get_data()
    current_order_id = state_data.get('current_order_id')
    
    if not current_order_id:
        await message.reply("Ошибка: неизвестный заказ. Пожалуйста, начните сначала.")
        return
    
    # Получаем ID фото
    if message.photo:
        # Берем фото максимального качества
        photo_id = message.photo[-1].file_id
        await message.reply(f"Фото заказа {current_order_id} получено. Можете отправить еще или нажмите 'Подтвердить готовность'.")
    else:
        await message.reply("Пожалуйста, отправьте именно фотографию заказа.")


async def handle_confirm_ready_callback(
    callback: CallbackQuery,
    state: FSMContext
):
    """
    Обработчик подтверждения готовности заказа.
    """
    order_id = callback.data.split('_')[2]  # confirm_ready_{order_id}
    
    # Здесь должен быть вызов use case для обновления статуса заказа
    # Пока просто показываем сообщение
    await callback.message.edit_text(
        f"Заказ {order_id} отмечен как готов к доставке.\n"
        f"Курьер будет направлен."
    )
    
    # Сбрасываем состояние
    await state.clear()
    
    await callback.answer("Заказ готов к доставке")


@inject
async def handle_cooking_time_message(
    message: Message,
    state: FSMContext,
    set_cooking_time_use_case: SetCookingTimeUseCase = Provide["set_cooking_time_use_case"],
    warehouse_repository: IWarehouseRepository = Provide["warehouse_repository"]
):
    """
    Обработчик ввода времени готовки вручную.
    """
    try:
        cooking_time_minutes = int(message.text)
        
        if cooking_time_minutes <= 0 or cooking_time_minutes > 180:
            await message.reply("Пожалуйста, укажите время в минутах (1–180).")
            return
        
        # Получаем склад по chat_id
        warehouse = await warehouse_repository.get_by_telegram_chat_id(message.chat.id)
        if not warehouse:
            await message.reply("Склад не найден. Сначала активируйте склад.")
            return
        
        # Получаем order_id из состояния
        state_data = await state.get_data()
        current_order_id = state_data.get('current_order_id')
        
        if not current_order_id:
            await message.reply("Ошибка: неизвестный заказ. Пожалуйста, начните сначала.")
            return
        
        dto = SetCookingTimeDTO(
            order_id=current_order_id,
            warehouse_id=warehouse.id,
            chat_id=message.chat.id,
            cooking_time_minutes=cooking_time_minutes
        )
        
        order = await set_cooking_time_use_case.execute(dto)
        
        await message.reply(
            f"Время готовности заказа {current_order_id}: {order.cooking_time_minutes} минут "
            f"(ожидаемое время готовности: {order.expected_ready_at.strftime('%H:%M') if order.expected_ready_at else 'N/A'})."
        )
        
        # Меняем состояние на ожидание фото
        await state.set_state(OrderProcessing.waiting_for_photos)
        
    except ValueError:
        await message.reply("Пожалуйста, введите целое число минут (например, 25).")
    except Exception as e:
        await message.reply(f"Ошибка при установке времени готовности: {str(e)}")


def setup_order_handlers(dp: Dispatcher):
    """
    Настраивает обработчики заказов.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.callback_query.register(handle_new_order_callback, lambda c: c.data.startswith('accept_order_'))
    dp.callback_query.register(handle_cancel_order_callback, lambda c: c.data.startswith('cancel_order_'))
    dp.callback_query.register(handle_cooking_time_callback, lambda c: c.data.startswith('cooking_time_'))
    dp.callback_query.register(handle_ready_for_delivery_callback, lambda c: c.data.startswith('ready_for_delivery_'))
    dp.callback_query.register(handle_confirm_ready_callback, lambda c: c.data.startswith('confirm_ready_'))
    
    # Обработчик сообщений с фото
    dp.message.register(handle_photo_upload, lambda m: m.photo is not None)
    
    # Обработчик ввода времени готовки
    dp.message.register(handle_cooking_time_message, OrderProcessing.waiting_for_cooking_time)