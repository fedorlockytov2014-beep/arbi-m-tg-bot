from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.warehouse import Warehouse


class WarehouseRepository(ABC):
    """
    Абстрактный репозиторий для работы со складами.
    """
    
    @abstractmethod
    async def get_by_uid(self, uid: str) -> Optional[Warehouse]:
        """
        Получает склад по UID.
        
        Args:
            uid: UID склада
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass
    
    @abstractmethod
    async def get_by_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID чата.
        
        Args:
            chat_id: ID чата
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass
    
    @abstractmethod
    async def get_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Получает склад по коду активации.
        
        Args:
            activation_code: Код активации
            
        Returns:
            Warehouse: Склад или None если не найден
        """
        pass
    
    @abstractmethod
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет информацию о складе.
        
        Args:
            warehouse: Обновленный склад
            
        Returns:
            Warehouse: Обновленный склад
        """
        pass