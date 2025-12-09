from aiogram import Dispatcher
from aiogram.types import Message

from ....application.dto.statistics import TodayStatisticsDTO
from ....application.use_cases.statistics import GetTodayStatisticsUseCase


async def get_today_statistics_command(message: Message, get_today_statistics_use_case: GetTodayStatisticsUseCase):
    """
    Обработчик команды получения статистики за сегодня.
    
    Пример: /stats_today
    """
    # Создаем DTO для получения статистики за сегодня
    dto = TodayStatisticsDTO(
        warehouse_uid="default_warehouse",  # В реальном приложении будет определен из контекста
        chat_id=message.chat.id
    )
    
    try:
        # Выполняем получение статистики
        stats = await get_today_statistics_use_case.execute(dto)
        
        # Формируем сообщение со статистикой
        stats_message = (
            f"📊 Статистика за сегодня:\n\n"
            f"📦 Заказов: {stats['total_orders']}\n"
            f"💰 Выручка: {stats['total_revenue']} ₽\n"
            f"📊 Средний чек: {stats['avg_check']:.2f} ₽"
        )
        
        await message.reply(stats_message)
        
    except Exception as e:
        await message.reply(f"Ошибка при получении статистики: {str(e)}")


def setup_statistics_handlers(dp: Dispatcher):
    """
    Настраивает обработчики статистики.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(get_today_statistics_command, lambda m: m.text.startswith('/stats_today'))