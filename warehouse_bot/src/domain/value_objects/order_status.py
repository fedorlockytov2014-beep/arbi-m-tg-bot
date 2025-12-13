from enum import Enum

from warehouse_bot.config.settings import settings


class OrderStatus(str, Enum):
    """
    Перечисление статусов заказа.
    
    Attributes:
        NEW: новый заказ (создан в системе, ещё не отправлен в бот / или только что отправлен)
        SENT_TO_PARTNER: заказ отправлен в Telegram-бот партнёра
        ACCEPTED_BY_PARTNER: партнёр нажал «Взять заказ»
        COOKING: партнёр указал время готовности, заказ в процессе приготовления
        READY_FOR_DELIVERY: партнёр отправил фото и подтвердил готовность
        ON_DELIVERY: (опционально) заказ забрал курьер
        DELIVERED: заказ доставлен клиенту
        CANCELLED: заказ отменён (клиентом, курьером, партнёром или админом)
    """
    NEW = "new"
    SENT_TO_PARTNER = "sent_to_partner"
    ACCEPTED_BY_PARTNER = "accepted_by_partner"
    COOKING = "cooking"
    READY_FOR_DELIVERY = "ready_for_delivery"
    ON_DELIVERY = "on_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

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
