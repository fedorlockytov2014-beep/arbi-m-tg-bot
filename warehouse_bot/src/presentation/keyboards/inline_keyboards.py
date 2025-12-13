from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_order_actions_keyboard(order_id: str):
    """Клавиатура с действиями для заказа."""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✅ Взять заказ",
        callback_data=f"accept_order_{order_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        text="❌ Отменить заказ",
        callback_data=f"cancel_order_{order_id}"
    ))
    return keyboard.as_markup()


def get_accepted_order_keyboard(accepted_by: str, accepted_at: str):
    """Клавиатура для принятого заказа."""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=f"Заказ принят ({accepted_by}); {accepted_at}",
        callback_data="order_accepted_info"  # This is just a placeholder, no action needed
    ))
    return keyboard.as_markup()


def get_cooking_time_keyboard():
    """Клавиатура с вариантами времени приготовления."""
    keyboard = InlineKeyboardBuilder()
    times = [10, 20, 30, 45, 60]
    for time in times:
        keyboard.add(InlineKeyboardButton(
            text=f"{time} мин",
            callback_data=f"cooking_time_{time}"
        ))
    return keyboard.as_markup()


def get_ready_for_delivery_keyboard(order_id: str):
    """Клавиатура для подтверждения готовности заказа."""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="📦 Заказ готов",
        callback_data=f"ready_for_delivery_{order_id}"
    ))
    return keyboard.as_markup()


def get_confirm_ready_keyboard(order_id: str):
    """Клавиатура для подтверждения готовности с фото."""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✅ Подтвердить готовность",
        callback_data=f"confirm_ready_{order_id}"
    ))
    keyboard.add(InlineKeyboardButton(
        text="🔄 Изменить фотографии",
        callback_data=f"change_photos_{order_id}"
    ))
    return keyboard.as_markup()


def get_month_year_selection_keyboard():
    """Клавиатура для выбора месяца и года."""
    keyboard = InlineKeyboardBuilder()
    
    # Месяцы
    months = [
        ("Янв", "month_1"), ("Фев", "month_2"), ("Мар", "month_3"),
        ("Апр", "month_4"), ("Май", "month_5"), ("Июн", "month_6"),
        ("Июл", "month_7"), ("Авг", "month_8"), ("Сен", "month_9"),
        ("Окт", "month_10"), ("Ноя", "month_11"), ("Дек", "month_12")
    ]
    
    for month_text, callback_data in months:
        keyboard.add(InlineKeyboardButton(text=month_text, callback_data=callback_data))
    
    # Годы
    from datetime import datetime
    current_year = datetime.now().year
    keyboard.add(InlineKeyboardButton(text=str(current_year), callback_data=f"year_{current_year}"))
    keyboard.add(InlineKeyboardButton(text=str(current_year - 1), callback_data=f"year_{current_year - 1}"))
    
    return keyboard.as_markup()


def get_statistics_period_keyboard():
    """Клавиатура для выбора периода статистики."""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📅 За сегодня", callback_data="stats_today"))
    keyboard.add(InlineKeyboardButton(text="📈 За неделю", callback_data="stats_week"))
    keyboard.add(InlineKeyboardButton(text="📆 За месяц", callback_data="stats_month"))
    return keyboard.as_markup()