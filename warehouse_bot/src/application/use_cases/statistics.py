from datetime import datetime, timedelta
from typing import Dict, Union, List, Any, Tuple

from warehouse_bot.config.settings import settings
from ...application.dto.statistics import (
    MonthlyStatisticsDTO,
    TodayStatisticsDTO,
    WeeklyStatisticsDTO
)
from ...application.exceptions import StatisticsCalculationError, WarehouseNotFoundException
from ...domain.repositories.crm_repository import ICRMClient
from ...domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ...domain.repositories.warehouse_repository import IWarehouseRepository
from ...domain.value_objects import OrderStatus
from ...infrastructure.cache.stats_cache import StatsCache
from ...infrastructure.logging import get_logger

logger = get_logger(__name__)


def _extract_statistics_from_crm_response(orders_data: List[Dict[str, Any]]) -> Dict[str, Union[int, float]]:
    """
    Извлекает и агрегирует статистику из списка заказов, полученного от CRM.

    Args:
        orders_data: Список заказов в формате CRM (обычно под ключом 'data').

    Returns:
        Словарь с агрегированной статистикой: total_orders, total_revenue, avg_check.
    """
    if not isinstance(orders_data, list):
        orders_data = []

    total_orders = len(orders_data)
    total_revenue = 0.0

    for item in orders_data:
        try:
            amount = float(item.get('attributes', {}).get('total_amount', 0))
            total_revenue += amount
        except (TypeError, ValueError) as e:
            logger.warning("Некорректное значение total_amount в заказе", order=item, error=str(e))

    avg_check = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0
    total_revenue = round(total_revenue, 2)

    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "avg_check": avg_check,
    }


async def _validate_warehouse_access(
    warehouse_db_repo: IWarehouseDBRepository,
    warehouse_id: int | str,
    chat_id: int
) -> None:
    """
    Проверяет, существует ли склад и привязан ли он к указанному Telegram-чату.

    Raises:
        WarehouseNotFoundException: если склад не найден или не привязан.
    """
    db_warehouse = await warehouse_db_repo.get_by_id(warehouse_id)
    if not db_warehouse:
        await logger.error("Склад не найден в локальной БД", warehouse_id=warehouse_id)
        raise WarehouseNotFoundException(f"Склад с ID {warehouse_id} не найден")

    if db_warehouse.telegram_chat_id != chat_id:
        await logger.error(
            "Попытка доступа к статистике чужого склада",
            warehouse_id=warehouse_id,
            chat_id=chat_id,
            registered_chat=db_warehouse.telegram_chat_id
        )
        raise WarehouseNotFoundException(
            f"Склад с ID {warehouse_id} не привязан к данному чату"
        )


def _get_included_statuses() -> List[OrderStatus]:
    """
    Возвращает список статусов заказов, учитываемых при расчёте статистики.
    """
    return getattr(
        settings,
        'statistics.included_statuses',
        [OrderStatus.ON_DELIVERY, OrderStatus.DELIVERED]
    )


async def _fetch_and_aggregate_crm_stats(
    crm_client: ICRMClient,
    warehouse_id: int,
    date_from: str,
    date_to: str,
    statuses: List[OrderStatus]
) -> Dict[str, Union[int, float]]:
    """
    Выполняет запрос к CRM и агрегирует статистику.

    Raises:
        StatisticsCalculationError: при ошибках взаимодействия с CRM.
    """
    try:
        async with crm_client as crm:
            crm_response = await crm.get_sales_statistics(
                warehouse_id=warehouse_id,
                date_from=date_from,
                date_to=date_to,
                statuses=statuses
            )
    except Exception as e:
        await logger.error(
            "Ошибка при вызове CRM для статистики",
            warehouse_id=warehouse_id,
            error=str(e),
            exc_info=True
        )
        raise StatisticsCalculationError(f"Не удалось получить данные из CRM: {str(e)}") from e

    orders_data = crm_response.get('data', [])
    return _extract_statistics_from_crm_response(orders_data)


def _get_today_range_utc() -> Tuple[datetime, datetime]:
    """Возвращает начало и конец текущего дня в UTC."""
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end


def _get_current_week_range_utc() -> Tuple[datetime, datetime]:
    """Возвращает понедельник и воскресенье текущей недели в UTC."""
    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = (week_start + timedelta(days=6)).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )
    return week_start, week_end


def _get_current_month_range_utc() -> Tuple[datetime, datetime]:
    """Возвращает начало и конец текущего месяца в UTC."""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        month_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(microseconds=1)
    else:
        month_end = now.replace(month=now.month + 1, day=1) - timedelta(microseconds=1)
    return month_start, month_end


class GetTodayStatisticsUseCase:
    """
    Use case для получения статистики за текущий день (UTC).

    Отвечает за:
    - Валидацию привязки склада к Telegram-чату
    - Формирование временного диапазона "сегодня"
    - Получение данных из кеша или CRM
    - Безопасную агрегацию статистики
    - Кеширование результата на короткое время

    Примечание: не использует фиктивные/демонстрационные данные — только реальные или нулевые.
    """

    def __init__(
            self,
            warehouse_repository: IWarehouseRepository,
            warehouse_db_repository: IWarehouseDBRepository,
            stats_cache: StatsCache,
            crm_client: ICRMClient,
    ):
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.stats_cache = stats_cache
        self.crm_client = crm_client

    async def execute(self, data: TodayStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        await logger.info(
            "Начало получения статистики за сегодня",
            warehouse_id=data.warehouse_id,
            chat_id=data.chat_id
        )

        await _validate_warehouse_access(self.warehouse_db_repository, data.warehouse_id, data.chat_id)

        today_start, today_end = _get_today_range_utc()
        date_from = today_start.isoformat() + "Z"
        date_to = today_end.isoformat() + "Z"

        cache_key = f"stats:today:{data.warehouse_id}:{today_start.date().isoformat()}"
        cached_stats = await self.stats_cache.get(cache_key)
        if cached_stats:
            await logger.debug("Статистика за сегодня взята из кеша", warehouse_id=data.warehouse_id)
            return cached_stats

        await logger.debug("Запрос статистики за сегодня из CRM", warehouse_id=data.warehouse_id)

        included_statuses = _get_included_statuses()
        stats = await _fetch_and_aggregate_crm_stats(
            self.crm_client, data.warehouse_id, date_from, date_to, included_statuses
        )

        result = {
            "warehouse_id": data.warehouse_id,
            "total_orders": stats["total_orders"],
            "total_revenue": stats["total_revenue"],
            "avg_check": stats["avg_check"],
            "date": today_start.date().isoformat()
        }

        await self.stats_cache.set(key=cache_key, value=result, ttl=60)
        await logger.info(
            "Статистика за сегодня успешно получена",
            warehouse_id=data.warehouse_id,
            orders=stats["total_orders"],
            revenue=stats["total_revenue"]
        )

        return result


class GetWeeklyStatisticsUseCase:
    """
    Use case для получения статистики за текущую неделю (ПН–ВС по UTC).

    Аналогичен дневной статистике, но с другим временным окном и TTL кеша.
    """

    def __init__(
            self,
            warehouse_repository: IWarehouseRepository,
            warehouse_db_repository: IWarehouseDBRepository,
            stats_cache: StatsCache,
            crm_client: ICRMClient,
    ):
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.stats_cache = stats_cache
        self.crm_client = crm_client

    async def execute(self, data: WeeklyStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        await logger.info("Начало получения недельной статистики", warehouse_id=data.warehouse_id)

        await _validate_warehouse_access(self.warehouse_db_repository, data.warehouse_id, data.chat_id)

        week_start, week_end = _get_current_week_range_utc()
        date_from = week_start.isoformat() + "Z"
        date_to = week_end.isoformat() + "Z"

        cache_key = f"stats:week:{data.warehouse_id}:{week_start.date().isoformat()}"
        cached_stats = await self.stats_cache.get(cache_key)
        if cached_stats:
            return cached_stats

        included_statuses = _get_included_statuses()
        stats = await _fetch_and_aggregate_crm_stats(
            self.crm_client, data.warehouse_id, date_from, date_to, included_statuses
        )

        result = {
            "warehouse_id": data.warehouse_id,
            "total_orders": stats["total_orders"],
            "total_revenue": stats["total_revenue"],
            "avg_check": stats["avg_check"],
            "date_range": f"{week_start.date().isoformat()} - {week_end.date().isoformat()}"
        }

        await self.stats_cache.set(key=cache_key, value=result, ttl=300)  # 5 минут
        await logger.info("Недельная статистика успешно получена", warehouse_id=data.warehouse_id)
        return result


class GetMonthlyStatisticsUseCase:
    """
    Use case для получения статистики за текущий календарный месяц (UTC).
    """

    def __init__(
            self,
            warehouse_repository: IWarehouseRepository,
            warehouse_db_repository: IWarehouseDBRepository,
            stats_cache: StatsCache,
            crm_client: ICRMClient,
    ):
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.stats_cache = stats_cache
        self.crm_client = crm_client

    async def execute(self, data: MonthlyStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        await logger.info("Начало получения месячной статистики", warehouse_id=data.warehouse_id)

        await _validate_warehouse_access(self.warehouse_db_repository, data.warehouse_id, data.chat_id)

        month_start, month_end = _get_current_month_range_utc()
        date_from = month_start.isoformat() + "Z"
        date_to = month_end.isoformat() + "Z"

        cache_key = f"stat2s:month:{data.warehouse_id}:{month_start.date().isoformat()}"
        cached_stats = await self.stats_cache.get(cache_key)
        if cached_stats:
            await logger.debug(message="Статистика получена из кэша", cached_stats=cached_stats)
            return cached_stats

        included_statuses = _get_included_statuses()
        stats = await _fetch_and_aggregate_crm_stats(
            self.crm_client, data.warehouse_id, date_from, date_to, included_statuses
        )
        await logger.debug(message="Статистика получена от CRM", stats=stats)

        result = {
            "warehouse_id": data.warehouse_id,
            "total_orders": stats["total_orders"],
            "total_revenue": stats["total_revenue"],
            "avg_check": stats["avg_check"],
            "date_range": f"{month_start.date().isoformat()} - {month_end.date().isoformat()}"
        }

        await self.stats_cache.set(key=cache_key, value=result, ttl=1800)  # 30 минут
        await logger.info("Месячная статистика успешно получена", warehouse_id=data.warehouse_id)
        return result
