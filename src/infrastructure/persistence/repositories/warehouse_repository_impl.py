from typing import List, Optional

from src.domain.entities.warehouse import Warehouse
from src.domain.repositories.warehouse_repository import WarehouseRepository
from src.infrastructure.cache.redis_cache import RedisCache


class WarehouseRepositoryImpl(WarehouseRepository):
    """
    Реализация репозитория склада.
    """
    
    def __init__(self, engine, cache: RedisCache):
        self.engine = engine
        self.cache = cache
    
    async def get_by_uid(self, uid: str) -> Optional[Warehouse]:
        """
        Получает склад по UID.
        
        Args:
            uid: UID склада
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        # Попробуем получить из кеша
        cached = await self.cache.get(f"warehouse:uid:{uid}")
        if cached:
            return Warehouse(**cached)
        
        # В реальной реализации здесь будет запрос к БД
        # Для демонстрации возвращаем заглушку
        if uid == "test-warehouse":
            warehouse = Warehouse(
                uid=uid,
                name="Тестовый склад",
                address="Тестовый адрес",
                telegram_chat_id=None
            )
            # Сохраняем в кеш
            await self.cache.set(f"warehouse:uid:{uid}", warehouse.__dict__, ttl=3600)
            return warehouse
        
        return None
    
    async def get_by_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID чата.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        # В реальной реализации будет запрос к БД
        # Для демонстрации возвращаем заглушку
        if chat_id == 123456789:
            warehouse = Warehouse(
                uid="test-warehouse",
                name="Тестовый склад",
                address="Тестовый адрес",
                telegram_chat_id=chat_id
            )
            return warehouse
        
        return None
    
    async def get_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Получает склад по коду активации.
        
        Args:
            activation_code: Код активации
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        # В реальной реализации будет запрос к БД
        # Для демонстрации возвращаем заглушку
        if activation_code == "TEST_CODE":
            warehouse = Warehouse(
                uid="test-warehouse",
                name="Тестовый склад",
                address="Тестовый адрес",
                telegram_chat_id=None
            )
            return warehouse
        
        return None
    
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет информацию о складе.
        
        Args:
            warehouse: Обновленный склад
            
        Returns:
            Warehouse: Обновленный склад
        """
        # В реальной реализации будет запрос к БД
        # Для демонстрации просто возвращаем переданный объект
        # и обновляем кеш
        await self.cache.set(f"warehouse:uid:{warehouse.uid}", warehouse.__dict__, ttl=3600)
        return warehouse