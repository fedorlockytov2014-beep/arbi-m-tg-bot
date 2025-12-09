from typing import List, Optional

from ....domain.entities.warehouse import Warehouse
from ....domain.repositories.warehouse_repository import WarehouseRepository


class WarehouseRepositoryImpl(WarehouseRepository):
    """
    Реализация репозитория складов.
    В реальном приложении будет использовать базу данных (например, SQLAlchemy).
    """
    
    def __init__(self):
        """
        Инициализирует репозиторий.
        В реальном приложении здесь будет подключение к базе данных.
        """
        # Для демонстрации используем простое хранилище в памяти
        self._warehouses: dict[str, Warehouse] = {}
    
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """
        Получает склад по ID.
        """
        for warehouse in self._warehouses.values():
            if str(warehouse.id) == warehouse_id:
                return warehouse
        return None
    
    async def get_by_uid(self, warehouse_uid: str) -> Optional[Warehouse]:
        """
        Получает склад по UID.
        """
        return self._warehouses.get(warehouse_uid)
    
    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID Telegram-чата.
        """
        for warehouse in self._warehouses.values():
            if warehouse.telegram_chat_id == chat_id:
                return warehouse
        return None
    
    async def get_all(self) -> List[Warehouse]:
        """
        Получает все склады.
        """
        return list(self._warehouses.values())
    
    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохраняет склад.
        """
        self._warehouses[warehouse.uid] = warehouse
        return warehouse
    
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет склад.
        """
        self._warehouses[warehouse.uid] = warehouse
        return warehouse
    
    async def delete(self, warehouse_id: str) -> bool:
        """
        Удаляет склад.
        """
        for uid, warehouse in self._warehouses.items():
            if str(warehouse.id) == warehouse_id:
                del self._warehouses[uid]
                return True
        return False
    
    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации.
        """
        for warehouse in self._warehouses.values():
            if warehouse.activation_code == activation_code:
                return warehouse
        return None