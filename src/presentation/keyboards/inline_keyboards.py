from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def get_accept_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для принятия заказа"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Взять заказ",
        callback_data=f"accept_order_{order_id}"
    )
    builder.button(
        text="❌ Отменить",
        callback_data=f"cancel_order_{order_id}"
    )
    builder.adjust(2)
    return builder.as_markup()


def get_cooking_time_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени готовки"""
    builder = InlineKeyboardBuilder()
    times = [10, 20, 30, 45, 60]
    for time in times:
        builder.button(
            text=f"{time} мин",
            callback_data=f"cooking_time_{time}"
        )
    builder.adjust(3)
    return builder.as_markup()


def get_order_ready_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения готовности заказа"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📦 Заказ готов",
        callback_data=f"order_ready_{order_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_ready_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения готовности с фото"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить готовность",
        callback_data=f"confirm_ready_{order_id}"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Основное меню бота"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="📦 Новые заказы",
        callback_data="show_new_orders"
    )
    builder.button(
        text="📊 Статистика",
        callback_data="show_statistics"
    )
    builder.button(
        text="⚙️ Настройки",
        callback_data="show_settings"
    )
    builder.adjust(1)
    return builder.as_markup()