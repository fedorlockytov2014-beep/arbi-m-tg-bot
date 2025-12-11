from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.warehouse import Warehouse


class WarehouseRepository(ABC):
    """
    Абстрактный репозиторий для работы со складами.
    """

    @abstractmethod
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """
        Получает склад по ID.
        
        Args:
            warehouse_id: ID склада
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass

    @abstractmethod
    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID Telegram-чата.
        
        Args:
            chat_id: ID Telegram-чата
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass

    @abstractmethod
    async def get_all(self) -> List[Warehouse]:
        """
        Получает все склады.
        
        Returns:
            List[Warehouse]: Список складов
        """
        pass

    @abstractmethod
    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохраняет склад.
        
        Args:
            warehouse: Склад для сохранения
            
        Returns:
            Warehouse: Сохранённый склад
        """
        pass

    @abstractmethod
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет склад.
        
        Args:
            warehouse: Склад для обновления
            
        Returns:
            Warehouse: Обновлённый склад
        """
        pass

    @abstractmethod
    async def delete(self, warehouse_id: str) -> bool:
        """
        Удаляет склад.
        
        Args:
            warehouse_id: ID склада для удаления
            
        Returns:
            bool: True если склад был удалён, иначе False
        """
        pass

    @abstractmethod
    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации.
        
        Args:
            activation_code: Код активации
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass