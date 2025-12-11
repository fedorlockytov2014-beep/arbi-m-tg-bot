from datetime import datetime, timedelta
from typing import Dict, Union

from ...application.dto.statistics import (
    MonthlyStatisticsDTO,
    TodayStatisticsDTO,
    WeeklyStatisticsDTO
)
from ...application.exceptions import StatisticsCalculationError, WarehouseNotFoundException
from ...domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ...domain.repositories.warehouse_repository import IWarehouseRepository
from ...infrastructure.cache.stats_cache import StatsCache
from ...infrastructure.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)

class GetTodayStatisticsUseCase:
    """
    Use case для получения статистики за сегодня.
    
    Отвечает за:
    - Получение данных о складе
    - Формирование периода за сегодня
    - Получение статистики из кеша или CRM
    - Кеширование результатов
    
    Атрибуты:
        warehouse_repository: Репозиторий для работы со складами
        stats_cache: Сервис кеширования статистики
    """
    
    def __init__(
        self,
        warehouse_repository: IWarehouseRepository,
        warehouse_db_repository: IWarehouseDBRepository,
        stats_cache: StatsCache,
        crm_client,
    ):
        """
        Инициализирует use case.
        
        Args:
            warehouse_repository: Репозиторий для работы со складами
            warehouse_db_repository: Репозиторий для работы с локальной БД складов
            stats_cache: Сервис кеширования статистики
            crm_client: Клиент для интеграции с CRM
        """
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.stats_cache = stats_cache
        self.crm_client = crm_client
        
    async def execute(self, data: TodayStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        """
        Выполняет сценарий получения статистики за сегодня.
        
        Args:
            data: DTO с данными для получения статистики
            
        Returns:
            Dict[str, Union[int, float, str]]: Статистика за сегодня
            
        Raises:
            WarehouseNotFoundException: Если склад не найден
            StatisticsCalculationError: При ошибках расчета статистики
        """
        await logger.info(
            "Начало получения статистики за сегодня",
            warehouse_id=data.warehouse_id,
            chat_id=data.chat_id
        )
        
        # Проверка, что склад существует и привязан к чату
        crm_warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not crm_warehouse:
            await logger.error(
                "Склад не найден при запросе статистики",
                warehouse_id=data.warehouse_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")

        db_warehouse = await self.warehouse_db_repository.get_by_id(data.warehouse_id)
        if not db_warehouse:
            await logger.error(
                "Склад не найден при запросе статистики",
                warehouse_id=data.warehouse_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")

        if db_warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка получить статистику для чужого склада",
                warehouse_id=data.warehouse_id,
                chat_id=data.chat_id,
                warehouse_chat_id=db_warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение текущей даты в UTC
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Форматирование дат для запроса
        date_from = today_start.isoformat() + "Z"
        date_to = today_end.isoformat() + "Z"
        
        try:
            # Попытка получить статистику из кеша
            cache_key = f"stats:today:{data.warehouse_id}:{today_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                await logger.debug(
                    "Статистика за сегодня получена из кеша",
                    warehouse_id=data.warehouse_id,
                    cache_key=cache_key
                )
                return cached_stats
                
            # Если нет в кеше - получаем из CRM
            await logger.debug(
                "Получение статистики за сегодня из CRM",
                warehouse_id=data.warehouse_id,
                date_from= date_from,
                date_to=date_to
            )
            
            # Получаем статусы из настроек
            included_statuses = getattr(settings, 'statistics.included_statuses', ['ready_for_delivery', 'on_delivery', 'delivered'])
            excluded_statuses = getattr(settings, 'statistics.excluded_statuses', ['cancelled', 'new', 'sent_to_partner', 'accepted_by_partner', 'cooking'])
            
            # Получаем статистику из CRM
            async with self.crm_client as crm:
                stats_data = await crm.get_sales_statistics(
                    warehouse_id=data.warehouse_id,
                    date_from=date_from,
                    date_to=date_to,
                    statuses=included_statuses
                )
                
                # Обработка данных из CRM
                total_orders = len(stats_data.get('data', []))
                total_revenue = sum(
                    float(item.get('attributes', {}).get('total_amount', 0)) 
                    for item in stats_data.get('data', [])
                )
                avg_check = total_revenue / total_orders if total_orders > 0 else 0

            # Если не удалось получить из CRM, используем тестовые данные
            if not stats_data or 'data' not in stats_data:
                stats_data = {
                    "warehouse_id": data.warehouse_id,
                    "total_orders": 18,
                    "total_revenue": 23540,
                    "avg_check": 1307.78,
                    "date": today_start.date().isoformat()
                }
            else:
                # Формируем финальные данные из CRM
                stats_data = {
                    "warehouse_id": data.warehouse_id,
                    "total_orders": total_orders,
                    "total_revenue": total_revenue,
                    "avg_check": avg_check,
                    "date": today_start.date().isoformat()
                }

            # Кеширование результатов
            await self.stats_cache.set(
                key=cache_key,
                value=stats_data,
                ttl=60  # 1 minute for demo
            )
            
            await logger.info(
                "Статистика за сегодня успешно получена",
                warehouse_id=data.warehouse_id,
                orders=stats_data["total_orders"],
                revenue=stats_data["total_revenue"]
            )
            
            return stats_data
            
        except Exception as e:
            await logger.error(
                "Ошибка при получении статистики за сегодня",
                warehouse_id=data.warehouse_id,
                error=str(e),
                exc_info=True
            )
            raise StatisticsCalculationError(
                f"Не удалось получить статистику за сегодня: {str(e)}"
            ) from e


class GetWeeklyStatisticsUseCase:
    """
    Use case для получения статистики за неделю.
    """
    
    def __init__(
        self,
        warehouse_repository: IWarehouseRepository,
        stats_cache: StatsCache,
    ):
        """
        Инициализирует use case.
        
        Args:
            warehouse_repository: Репозиторий для работы со складами
            stats_cache: Сервис кеширования статистики
        """
        self.warehouse_repository = warehouse_repository
        self.stats_cache = stats_cache
        
    async def execute(self, data: WeeklyStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        """
        Выполняет сценарий получения статистики за неделю.
        
        Args:
            data: DTO с данными для получения статистики за неделю
            
        Returns:
            Dict[str, Union[int, float, str]]: Статистика за неделю
            
        Raises:
            WarehouseNotFoundException: Если склад не найден
            StatisticsCalculationError: При ошибках расчета статистики
        """
        await logger.info(
            "Начало получения статистики за неделю",
            warehouse_id=data.warehouse_id,
            chat_id=data.chat_id
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при запросе статистики за неделю",
                warehouse_id=data.warehouse_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка получить статистику за неделю для чужого склада",
                warehouse_id=data.warehouse_id,
                chat_id=data.chat_id,
                warehouse_chat_id=warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение дат для недели
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = (week_start + timedelta(days=6)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Форматирование дат для запроса
        date_from = week_start.isoformat() + "Z"
        date_to = week_end.isoformat() + "Z"
        
        try:
            # Попытка получить статистику из кеша
            cache_key = f"stats:week:{data.warehouse_id}:{week_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                await logger.debug(
                    "Статистика за неделю получена из кеша",
                    warehouse_id=data.warehouse_id,
                    cache_key=cache_key
                )
                return cached_stats
                
            # Для примера используем тестовые данные
            stats_data = {
                "warehouse_id": data.warehouse_id,
                "total_orders": 126,
                "total_revenue": 164780,
                "avg_check": 1307.78,
                "date_range": f"{week_start.date().isoformat()} - {week_end.date().isoformat()}"
            }
            
            # Кеширование результатов
            await self.stats_cache.set(
                key=cache_key,
                value=stats_data,
                ttl=60  # 1 minute for demo
            )
            
            await logger.info(
                "Статистика за неделю успешно получена",
                warehouse_id=data.warehouse_id,
                orders=stats_data["total_orders"],
                revenue=stats_data["total_revenue"]
            )
            
            return stats_data
            
        except Exception as e:
            await logger.error(
                "Ошибка при получении статистики за неделю",
                warehouse_id=data.warehouse_id,
                error=str(e),
                exc_info=True
            )
            raise StatisticsCalculationError(
                f"Не удалось получить статистику за неделю: {str(e)}"
            ) from e


class GetMonthlyStatisticsUseCase:
    """
    Use case для получения статистики за месяц.
    """
    
    def __init__(
        self,
        warehouse_repository: IWarehouseRepository,
        stats_cache: StatsCache,
    ):
        """
        Инициализирует use case.
        
        Args:
            warehouse_repository: Репозиторий для работы со складами
            stats_cache: Сервис кеширования статистики
        """
        self.warehouse_repository = warehouse_repository
        self.stats_cache = stats_cache
        
    async def execute(self, data: MonthlyStatisticsDTO) -> Dict[str, Union[int, float, str]]:
        """
        Выполняет сценарий получения статистики за месяц.
        
        Args:
            data: DTO с данными для получения статистики за месяц
            
        Returns:
            Dict[str, Union[int, float, str]]: Статистика за месяц
            
        Raises:
            WarehouseNotFoundException: Если склад не найден
            StatisticsCalculationError: При ошибках расчета статистики
        """
        await logger.info(
            "Начало получения статистики за месяц",
            warehouse_id=data.warehouse_id,
            chat_id=data.chat_id
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при запросе статистики за месяц",
                warehouse_id=data.warehouse_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка получить статистику за месяц для чужого склада",
                warehouse_id=data.warehouse_id,
                chat_id=data.chat_id,
                warehouse_chat_id=warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение дат для месяца
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Последний день месяца
        if now.month == 12:
            month_end = now.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
            month_end = (next_month - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Форматирование дат для запроса
        date_from = month_start.isoformat() + "Z"
        date_to = month_end.isoformat() + "Z"
        
        try:
            # Попытка получить статистику из кеша
            cache_key = f"stats:month:{data.warehouse_id}:{month_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                await logger.debug(
                    "Статистика за месяц получена из кеша",
                    warehouse_id=data.warehouse_id,
                    cache_key=cache_key
                )
                return cached_stats
                
            # Для примера используем тестовые данные
            stats_data = {
                "warehouse_id": data.warehouse_id,
                "total_orders": 542,
                "total_revenue": 704600,
                "avg_check": 1300.00,
                "date_range": f"{month_start.date().isoformat()} - {month_end.date().isoformat()}"
            }
            
            # Кеширование результатов
            await self.stats_cache.set(
                key=cache_key,
                value=stats_data,
                ttl=900  # 15 minutes for demo
            )
            
            await logger.info(
                "Статистика за месяц успешно получена",
                warehouse_id=data.warehouse_id,
                orders=stats_data["total_orders"],
                revenue=stats_data["total_revenue"]
            )
            
            return stats_data
            
        except Exception as e:
            await logger.error(
                "Ошибка при получении статистики за месяц",
                warehouse_id=data.warehouse_id,
                error=str(e),
                exc_info=True
            )
            raise StatisticsCalculationError(
                f"Не удалось получить статистику за месяц: {str(e)}"
            ) from e