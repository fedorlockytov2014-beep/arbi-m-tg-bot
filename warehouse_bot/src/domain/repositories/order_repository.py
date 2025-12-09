from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.order import Order
from ..value_objects.order_status import OrderStatus


class OrderRepository(ABC):
    """
    Абстрактный репозиторий для работы с заказами.
    """

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Получает заказ по ID.
        
        Args:
            order_id: ID заказа
            
        Returns:
            Order: Заказ или None если не найден
        """
        pass

    @abstractmethod
    async def get_by_number(self, order_number: str) -> Optional[Order]:
        """
        Получает заказ по номеру.
        
        Args:
            order_number: Номер заказа
            
        Returns:
            Order: Заказ или None если не найден
        """
        pass

    @abstractmethod
    async def get_by_warehouse_and_status(
        self, 
        warehouse_id: str, 
        status: OrderStatus
    ) -> List[Order]:
        """
        Получает заказы по складу и статусу.
        
        Args:
            warehouse_id: ID склада
            status: Статус заказа
            
        Returns:
            List[Order]: Список заказов
        """
        pass

    @abstractmethod
    async def get_all_by_warehouse(self, warehouse_id: str) -> List[Order]:
        """
        Получает все заказы по складу.
        
        Args:
            warehouse_id: ID склада
            
        Returns:
            List[Order]: Список заказов
        """
        pass

    @abstractmethod
    async def save(self, order: Order) -> Order:
        """
        Сохраняет заказ.
        
        Args:
            order: Заказ для сохранения
            
        Returns:
            Order: Сохранённый заказ
        """
        pass

    @abstractmethod
    async def update(self, order: Order) -> Order:
        """
        Обновляет заказ.
        
        Args:
            order: Заказ для обновления
            
        Returns:
            Order: Обновлённый заказ
        """
        pass

    @abstractmethod
    async def delete(self, order_id: str) -> bool:
        """
        Удаляет заказ.
        
        Args:
            order_id: ID заказа для удаления
            
        Returns:
            bool: True если заказ был удалён, иначе False
        """
        pass

    @abstractmethod
    async def get_orders_by_status_for_period(
        self,
        warehouse_id: str,
        statuses: List[OrderStatus],
        date_from: str,
        date_to: str
    ) -> List[Order]:
        """
        Получает заказы по статусам за определённый период.
        
        Args:
            warehouse_id: ID склада
            statuses: Список статусов
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            
        Returns:
            List[Order]: Список заказов
        """
        pass