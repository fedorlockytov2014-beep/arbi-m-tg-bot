from enum import Enum

from warehouse_bot.config.settings import settings


class OrderStatus(str, Enum):
    """
    Перечисление статусов заказа.
    
    Attributes:
        NEW: Новый заказ, только поступил
        SENT_TO_PARTNER: Отправлен партнёру
        ACCEPTED_BY_PARTNER: Принят партнёром
        COOKING: Готовится
        READY_FOR_DELIVERY: Готов к доставке
        ON_DELIVERY: На доставке
        DELIVERED: Доставлен
        CANCELLED: Отменён
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
        
        # Если не найдено точное совпадение, пробуем найти по русским названиям
        status_mapping = {
            "new": cls.NEW,
            "sent_to_partner": cls.SENT_TO_PARTNER,
            "accepted_by_partner": cls.ACCEPTED_BY_PARTNER,
            "cooking": cls.COOKING,
            "ready_for_delivery": cls.READY_FOR_DELIVERY,
            "on_delivery": cls.ON_DELIVERY,
            "delivered": cls.DELIVERED,
            "cancelled": cls.CANCELLED,
            # Русские названия
            "Новый": cls.NEW,
            "Отправлен партнёру": cls.SENT_TO_PARTNER,
            "Принят партнёром": cls.ACCEPTED_BY_PARTNER,
            "Готовится": cls.COOKING,
            "Готов к доставке": cls.READY_FOR_DELIVERY,
            "На доставке": cls.ON_DELIVERY,
            "Доставлен": cls.DELIVERED,
            "Отменён": cls.CANCELLED,
            # Альтернативные названия из ТЗ
            "Ожидает сборки": cls.NEW,
            "Ожидает подтверждения": cls.ACCEPTED_BY_PARTNER,
            "Заказ подтвержден": cls.COOKING,
            "Заказ доставляется": cls.READY_FOR_DELIVERY,
            "Заказ завершен": cls.DELIVERED,
        }
        
        return status_mapping.get(value, cls.NEW)

    @classmethod
    def get_tracking_statuses(cls) -> list['OrderStatus']:
        """
        Возвращает статусы, которые отслеживаются в статистике.
        
        Returns:
            list[OrderStatus]: Список статусов для отслеживания
        """

        return [OrderStatus(value) for value in settings.statistics.included_statuses]

    @classmethod
    def get_non_tracking_statuses(cls) -> list['OrderStatus']:
        """
        Возвращает статусы, которые не отслеживаются в статистике.
        
        Returns:
            list[OrderStatus]: Список статусов, не учитываемых в статистике
        """

        return [OrderStatus(value) for value in settings.statistics.excluded_statuses]