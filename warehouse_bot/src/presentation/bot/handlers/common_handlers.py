from aiogram import Dispatcher
from aiogram.types import Message


async def start_command(message: Message):
    """
    Обработчик команды /start.
    """
    welcome_message = (
        "Добро пожаловать в бота управления складом!\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/activate <код> - Активировать склад по коду\n"
        "/accept_order <ID_заказа> - Принять заказ\n"
        "/set_cooking_time <ID_заказа> <минуты> - Установить время приготовления\n"
        "/stats_today - Получить статистику за сегодня\n"
        "/help - Помощь"
    )
    
    await message.reply(welcome_message)


async def help_command(message: Message):
    """
    Обработчик команды /help.
    """
    help_message = (
        "Помощь по работе с ботом:\n\n"
        "1. Сначала активируйте склад командой: /activate <код_активации>\n"
        "2. После активации вы можете принимать заказы: /accept_order <ID_заказа>\n"
        "3. Установите время приготовления: /set_cooking_time <ID_заказа> <минуты>\n"
        "4. Просматривайте статистику: /stats_today\n\n"
        "Для получения дополнительной информации обращайтесь к администратору."
    )
    
    await message.reply(help_message)


def setup_common_handlers(dp: Dispatcher):
    """
    Настраивает общие обработчики.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(start_command, lambda m: m.text.startswith('/start'))
    dp.message.register(help_command, lambda m: m.text.startswith('/help'))