from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_keyboard():
    """Клавиатура главного меню."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="📦 Новые заказы"))
    keyboard.add(KeyboardButton(text="📊 Статистика"))
    keyboard.add(KeyboardButton(text=" помощь"))
    keyboard.adjust(2, 1)  # 2 кнопки в первом ряду, 1 во втором
    return keyboard.as_markup(resize_keyboard=True)


def get_statistics_keyboard():
    """Клавиатура для выбора типа статистики."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="📅 За сегодня"))
    keyboard.add(KeyboardButton(text="📈 За неделю"))
    keyboard.add(KeyboardButton(text="📆 По месяцам"))
    keyboard.add(KeyboardButton(text="Назад"))
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)


def get_month_selection_keyboard():
    """Клавиатура для выбора месяца."""
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="📆 Текущий месяц"))
    keyboard.add(KeyboardButton(text="📆 Прошлый месяц"))
    keyboard.add(KeyboardButton(text="📅 Выбрать месяц"))
    keyboard.add(KeyboardButton(text="Назад"))
    keyboard.adjust(2, 2)
    return keyboard.as_markup(resize_keyboard=True)


def get_months_keyboard():
    """Клавиатура с месяцами."""
    keyboard = ReplyKeyboardBuilder()
    months = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    for month in months:
        keyboard.add(KeyboardButton(text=month))
    
    keyboard.add(KeyboardButton(text="Назад"))
    keyboard.adjust(3, 3, 3, 4)  # Распределяем кнопки по строкам
    return keyboard.as_markup(resize_keyboard=True)


def get_years_keyboard():
    """Клавиатура с годами."""
    keyboard = ReplyKeyboardBuilder()
    from datetime import datetime
    current_year = datetime.now().year
    keyboard.add(KeyboardButton(text=str(current_year)))
    keyboard.add(KeyboardButton(text=str(current_year - 1)))
    keyboard.add(KeyboardButton(text="Назад"))
    keyboard.adjust(2, 1)
    return keyboard.as_markup(resize_keyboard=True)