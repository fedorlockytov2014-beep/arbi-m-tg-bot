import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from ...application.dto.statistics import (
    MonthlyStatisticsDTO,
    StatisticsByDateRangeDTO,
    TodayStatisticsDTO,
    WeeklyStatisticsDTO
)
from ...application.exceptions import StatisticsCalculationError, WarehouseNotFoundException
from ...domain.repositories.warehouse_repository import WarehouseRepository
from ...infrastructure.cache.stats_cache import StatsCache

logger = logging.getLogger(__name__)

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
        warehouse_repository: WarehouseRepository,
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
        logger.info(
            "Начало получения статистики за сегодня",
            extra={
                "warehouse_uid": data.warehouse_uid,
                "chat_id": data.chat_id
            }
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            logger.error(
                "Склад не найден при запросе статистики",
                extra={
                    "warehouse_uid": data.warehouse_uid
                }
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            logger.error(
                "Попытка получить статистику для чужого склада",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с UID {data.warehouse_uid} не привязан к данному чату"
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
            cache_key = f"stats:today:{data.warehouse_uid}:{today_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                logger.debug(
                    "Статистика за сегодня получена из кеша",
                    extra={
                        "warehouse_uid": data.warehouse_uid,
                        "cache_key": cache_key
                    }
                )
                return cached_stats
                
            # Если нет в кеше - получаем из CRM
            logger.debug(
                "Получение статистики за сегодня из CRM",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "date_from": date_from,
                    "date_to": date_to
                }
            )
            
            # Здесь должен быть вызов CRM клиента для получения статистики
            # stats_data = await self.crm_client.get_sales_statistics(
            #     warehouse_id=data.warehouse_uid,
            #     date_from=date_from,
            #     date_to=date_to
            # )
            
            # Для примера используем тестовые данные
            stats_data = {
                "warehouse_id": data.warehouse_uid,
                "total_orders": 18,
                "total_revenue": 23540,
                "avg_check": 1307.78,
                "date": today_start.date().isoformat()
            }
            
            # Кеширование результатов
            await self.stats_cache.set(
                key=cache_key,
                value=stats_data,
                ttl=60  # 1 minute for demo
            )
            
            logger.info(
                "Статистика за сегодня успешно получена",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "orders": stats_data["total_orders"],
                    "revenue": stats_data["total_revenue"]
                }
            )
            
            return stats_data
            
        except Exception as e:
            logger.error(
                "Ошибка при получении статистики за сегодня",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "error": str(e),
                    "exc_info": True
                }
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
        warehouse_repository: WarehouseRepository,
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
        logger.info(
            "Начало получения статистики за неделю",
            extra={
                "warehouse_uid": data.warehouse_uid,
                "chat_id": data.chat_id
            }
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            logger.error(
                "Склад не найден при запросе статистики за неделю",
                extra={
                    "warehouse_uid": data.warehouse_uid
                }
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            logger.error(
                "Попытка получить статистику за неделю для чужого склада",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с UID {data.warehouse_uid} не привязан к данному чату"
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
            cache_key = f"stats:week:{data.warehouse_uid}:{week_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                logger.debug(
                    "Статистика за неделю получена из кеша",
                    extra={
                        "warehouse_uid": data.warehouse_uid,
                        "cache_key": cache_key
                    }
                )
                return cached_stats
                
            # Для примера используем тестовые данные
            stats_data = {
                "warehouse_id": data.warehouse_uid,
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
            
            logger.info(
                "Статистика за неделю успешно получена",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "orders": stats_data["total_orders"],
                    "revenue": stats_data["total_revenue"]
                }
            )
            
            return stats_data
            
        except Exception as e:
            logger.error(
                "Ошибка при получении статистики за неделю",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "error": str(e),
                    "exc_info": True
                }
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
        warehouse_repository: WarehouseRepository,
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
        logger.info(
            "Начало получения статистики за месяц",
            extra={
                "warehouse_uid": data.warehouse_uid,
                "chat_id": data.chat_id
            }
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            logger.error(
                "Склад не найден при запросе статистики за месяц",
                extra={
                    "warehouse_uid": data.warehouse_uid
                }
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            logger.error(
                "Попытка получить статистику за месяц для чужого склада",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с UID {data.warehouse_uid} не привязан к данному чату"
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
            cache_key = f"stats:month:{data.warehouse_uid}:{month_start.date().isoformat()}"
            cached_stats = await self.stats_cache.get(cache_key)
            
            if cached_stats:
                logger.debug(
                    "Статистика за месяц получена из кеша",
                    extra={
                        "warehouse_uid": data.warehouse_uid,
                        "cache_key": cache_key
                    }
                )
                return cached_stats
                
            # Для примера используем тестовые данные
            stats_data = {
                "warehouse_id": data.warehouse_uid,
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
            
            logger.info(
                "Статистика за месяц успешно получена",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "orders": stats_data["total_orders"],
                    "revenue": stats_data["total_revenue"]
                }
            )
            
            return stats_data
            
        except Exception as e:
            logger.error(
                "Ошибка при получении статистики за месяц",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "error": str(e),
                    "exc_info": True
                }
            )
            raise StatisticsCalculationError(
                f"Не удалось получить статистику за месяц: {str(e)}"
            ) from e