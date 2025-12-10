from dependency_injector import containers, providers
from dependency_injector.providers import Singleton, Factory

from ...application.use_cases.order_management import AcceptOrderUseCase, SetCookingTimeUseCase
from ...application.use_cases.warehouse_activation import ActivateWarehouseUseCase
from ...application.use_cases.statistics import GetTodayStatisticsUseCase, GetWeeklyStatisticsUseCase, GetMonthlyStatisticsUseCase
from ...domain.services.order_service import OrderService
from ...infrastructure.cache.stats_cache import StatsCache
from ...infrastructure.integrations.crm_client import CRMClient
from ...infrastructure.persistence.repositories.order_repository_impl import OrderRepositoryImpl
from ...infrastructure.persistence.repositories.warehouse_repository_impl import WarehouseRepositoryImpl


class Container(containers.DeclarativeContainer):
    """
    DI контейнер для приложения.
    """
    
    # Конфигурация
    config = providers.Configuration()
    
    # Сервисы
    order_service = Singleton(OrderService)
    
    # Репозитории
    order_repository = Singleton(
        OrderRepositoryImpl,
        crm_client=crm_client
    )
    warehouse_repository = Singleton(
        WarehouseRepositoryImpl,
        crm_client=crm_client
    )
    
    # Кеши
    stats_cache = Singleton(StatsCache)
    
    # Интеграции
    crm_client = Singleton(
        CRMClient,
        base_url=config.crm.base_url,
        api_token=config.crm.api_token,
        timeout=config.crm.timeout,
        max_retries=config.crm.max_retries,
        retry_delay=config.crm.retry_delay
    )
    
    # Use cases
    accept_order_use_case = Factory(
        AcceptOrderUseCase,
        order_repository=order_repository,
        warehouse_repository=warehouse_repository,
        order_service=order_service
    )
    
    set_cooking_time_use_case = Factory(
        SetCookingTimeUseCase,
        order_repository=order_repository,
        warehouse_repository=warehouse_repository,
        order_service=order_service
    )
    
    activate_warehouse_use_case = Factory(
        ActivateWarehouseUseCase,
        warehouse_repository=warehouse_repository
    )
    
    get_today_statistics_use_case = Factory(
        GetTodayStatisticsUseCase,
        warehouse_repository=warehouse_repository,
        stats_cache=stats_cache
    )
    
    get_weekly_statistics_use_case = Factory(
        GetWeeklyStatisticsUseCase,
        warehouse_repository=warehouse_repository,
        stats_cache=stats_cache
    )
    
    get_monthly_statistics_use_case = Factory(
        GetMonthlyStatisticsUseCase,
        warehouse_repository=warehouse_repository,
        stats_cache=stats_cache
    )