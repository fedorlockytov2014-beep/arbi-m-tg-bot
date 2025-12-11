from enum import Enum

from warehouse_bot.config.settings import settings


class OrderStatus(str, Enum):
    """
    Перечисление статусов заказа.
    
    Attributes:
        WAIT_FOR_ASSEMBLY: Новый заказ, Ожидает сборки
        WAIT_FOR_CONFIRMATION: Ожидает подтверждения
        ORDER_CONFIRMED: Заказ подтвержден
        ON_DELIVERY: Доставляется
        DELIVERED: Заказ завершен
    """
    WAIT_FOR_ASSEMBLY = "Ожидает сборки"
    WAIT_FOR_CONFIRMATION = "Ожидает подтверждения"
    ORDER_CONFIRMED = "Заказ подтвержден"
    ON_DELIVERY = "Доставляется"
    DELIVERED = "Заказ завершен"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, value: str) -> 'OrderStatus':
        """
        Создает OrderStatus из строкового значения.
        
        Args:
            value: Строковое значение статуса
            
        Returns:
            OrderStatus: Соответствующий enum-объект статуса
        """
        for status in cls:
            if status.value == value:
                return status
