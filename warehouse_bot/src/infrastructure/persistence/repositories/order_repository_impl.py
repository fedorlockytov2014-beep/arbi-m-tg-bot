from typing import List, Optional

from ....domain.entities.order import Order
from ....domain.repositories.order_repository import OrderRepository
from ....domain.value_objects.order_status import OrderStatus


class OrderRepositoryImpl(OrderRepository):
    """
    Реализация репозитория заказов.
    В реальном приложении будет использовать базу данных (например, SQLAlchemy).
    """
    
    def __init__(self):
        """
        Инициализирует репозиторий.
        В реальном приложении здесь будет подключение к базе данных.
        """
        # Для демонстрации используем простое хранилище в памяти
        self._orders: dict[str, Order] = {}
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Получает заказ по ID.
        """
        return self._orders.get(order_id)
    
    async def get_by_number(self, order_number: str) -> Optional[Order]:
        """
        Получает заказ по номеру.
        """
        for order in self._orders.values():
            if order.order_number == order_number:
                return order
        return None
    
    async def get_by_warehouse_and_status(
        self, 
        warehouse_id: str, 
        status: OrderStatus
    ) -> List[Order]:
        """
        Получает заказы по складу и статусу.
        """
        result = []
        for order in self._orders.values():
            if order.warehouse_id == warehouse_id and order.status == status:
                result.append(order)
        return result
    
    async def get_all_by_warehouse(self, warehouse_id: str) -> List[Order]:
        """
        Получает все заказы по складу.
        """
        result = []
        for order in self._orders.values():
            if order.warehouse_id == warehouse_id:
                result.append(order)
        return result
    
    async def save(self, order: Order) -> Order:
        """
        Сохраняет заказ.
        """
        self._orders[str(order.id)] = order
        return order
    
    async def update(self, order: Order) -> Order:
        """
        Обновляет заказ.
        """
        self._orders[str(order.id)] = order
        return order
    
    async def delete(self, order_id: str) -> bool:
        """
        Удаляет заказ.
        """
        if order_id in self._orders:
            del self._orders[order_id]
            return True
        return False
    
    async def get_orders_by_status_for_period(
        self,
        warehouse_id: str,
        statuses: List[OrderStatus],
        date_from: str,
        date_to: str
    ) -> List[Order]:
        """
        Получает заказы по статусам за определённый период.
        """
        result = []
        for order in self._orders.values():
            if (order.warehouse_id == warehouse_id and 
                order.status in statuses):
                # В реальном приложении здесь будет проверка дат
                result.append(order)
        return result