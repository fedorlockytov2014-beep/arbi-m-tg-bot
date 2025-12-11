from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from dependency_injector.wiring import inject, Provide

from ....application.dto.statistics import TodayStatisticsDTO, WeeklyStatisticsDTO, MonthlyStatisticsDTO
from ....application.use_cases.statistics import GetTodayStatisticsUseCase, GetWeeklyStatisticsUseCase, GetMonthlyStatisticsUseCase
from ....domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ....domain.repositories.warehouse_repository import IWarehouseRepository
from ...formatters.stats_formatter import format_today_statistics, format_weekly_statistics, format_monthly_statistics, format_error_statistics
from ....infrastructure.di.container import Container

@inject
async def stats_command(message: Message,
                        warehouse_repository: IWarehouseRepository = Provide[Container.warehouse_repository],
                        get_today_statistics_use_case: GetTodayStatisticsUseCase = Provide[Container.get_today_statistics_use_case],
                        **kwargs):
    """
    Обработчик команды /stats.
    """
    if not warehouse_repository or  not get_today_statistics_use_case:
        await message.reply("Ошибка: контейнер зависимостей не найден.")
        return

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

@inject
async def handle_stats_period_callback(callback: CallbackQuery,
                                       warehouse_repository: IWarehouseDBRepository = Provide[Container.warehouse_db_repository],
                                       get_today_statistics_use_case: GetTodayStatisticsUseCase = Provide[Container.get_today_statistics_use_case],
                                       get_weekly_statistics_use_case: GetWeeklyStatisticsUseCase = Provide[Container.get_weekly_statistics_use_case],
                                       get_monthly_statistics_use_case: GetMonthlyStatisticsUseCase = Provide[Container.get_monthly_statistics_use_case],
                                       **kwargs):
    """
    Обработчик выбора периода статистики.
    """
    period = callback.data.split('_')[1]  # stats_{period}
    # Получаем склад по chat_id
    warehouse = await warehouse_repository.get_by_telegram_chat_id(callback.message.chat.id)
    if not warehouse:
        await callback.answer("Склад не найден. Сначала активируйте склад.", show_alert=True)
        return
    
    try:
        if period == "today":
            dto = TodayStatisticsDTO(
                warehouse_id=warehouse.id,
                chat_id=callback.message.chat.id
            )
            stats = await get_today_statistics_use_case.execute(dto)
            response = format_today_statistics(stats)
            
        elif period == "week":
            dto = WeeklyStatisticsDTO(
                warehouse_id=warehouse.id,
                chat_id=callback.message.chat.id
            )
            stats = await get_weekly_statistics_use_case.execute(dto)
            response = format_weekly_statistics(stats)
            
        elif period == "month":
            dto = MonthlyStatisticsDTO(
                warehouse_id=warehouse.id,
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