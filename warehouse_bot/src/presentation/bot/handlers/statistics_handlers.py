from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ....application.dto.statistics import TodayStatisticsDTO, WeeklyStatisticsDTO, MonthlyStatisticsDTO
from ....application.use_cases.statistics import GetTodayStatisticsUseCase, GetWeeklyStatisticsUseCase, GetMonthlyStatisticsUseCase
from ....domain.repositories.warehouse_repository import WarehouseRepository
from ...formatters.stats_formatter import format_today_statistics, format_weekly_statistics, format_monthly_statistics, format_error_statistics


async def stats_command(message: Message, **kwargs):
    """
    Обработчик команды /stats.
    """
    # Получаем контейнер из kwargs
    container = kwargs.get('container')
    if not container:
        await message.reply("Ошибка: контейнер зависимостей не найден.")
        return
    
    # Получаем зависимости из контейнера
    warehouse_repository: WarehouseRepository = container.warehouse_repository()
    get_today_statistics_use_case: GetTodayStatisticsUseCase = container.get_today_statistics_use_case()
    
    # Проверяем, привязан ли чат к складу
    warehouse = await warehouse_repository.get_by_telegram_chat_id(message.chat.id)
    
    if not warehouse:
        await message.reply("Сначала активируйте склад. Используйте команду /start и перейдите по ссылке активации.")
        return
    
    # Показываем меню выбора статистики
    from ...keyboards.inline_keyboards import get_statistics_period_keyboard
    await message.reply(
        "📊 Статистика продаж\n\nВыберите период:",
        reply_markup=get_statistics_period_keyboard()
    )


async def handle_stats_period_callback(callback: CallbackQuery, **kwargs):
    """
    Обработчик выбора периода статистики.
    """
    # Получаем контейнер из kwargs
    container = kwargs.get('container')
    if not container:
        await callback.answer("Ошибка: контейнер зависимостей не найден.", show_alert=True)
        return
    
    # Получаем зависимости из контейнера
    warehouse_repository: WarehouseRepository = container.warehouse_repository()
    get_today_statistics_use_case: GetTodayStatisticsUseCase = container.get_today_statistics_use_case()
    get_weekly_statistics_use_case: GetWeeklyStatisticsUseCase = container.get_weekly_statistics_use_case()
    get_monthly_statistics_use_case: GetMonthlyStatisticsUseCase = container.get_monthly_statistics_use_case()
    
    period = callback.data.split('_')[1]  # stats_{period}
    
    # Получаем склад по chat_id
    warehouse = await warehouse_repository.get_by_telegram_chat_id(callback.message.chat.id)
    if not warehouse:
        await callback.answer("Склад не найден. Сначала активируйте склад.", show_alert=True)
        return
    
    try:
        if period == "today":
            dto = TodayStatisticsDTO(
                warehouse_uid=warehouse.uid,
                chat_id=callback.message.chat.id
            )
            stats = await get_today_statistics_use_case.execute(dto)
            response = format_today_statistics(stats)
            
        elif period == "week":
            dto = WeeklyStatisticsDTO(
                warehouse_uid=warehouse.uid,
                chat_id=callback.message.chat.id
            )
            stats = await get_weekly_statistics_use_case.execute(dto)
            response = format_weekly_statistics(stats)
            
        elif period == "month":
            dto = MonthlyStatisticsDTO(
                warehouse_uid=warehouse.uid,
                chat_id=callback.message.chat.id
            )
            stats = await get_monthly_statistics_use_case.execute(dto)
            response = format_monthly_statistics(stats)
            
        else:
            response = "Неверный период статистики."
        
        await callback.message.edit_text(response)
        
    except Exception as e:
        await callback.message.edit_text(format_error_statistics())
        await callback.answer(f"Ошибка получения статистики: {str(e)}", show_alert=True)


def setup_statistics_handlers(dp: Dispatcher):
    """
    Настраивает обработчики статистики.
    
    Args:
        dp: Диспетчер
    """
    # Регистрация обработчиков
    dp.message.register(stats_command, lambda m: m.text.startswith('/stats'))
    dp.callback_query.register(handle_stats_period_callback, lambda c: c.data.startswith('stats_'))