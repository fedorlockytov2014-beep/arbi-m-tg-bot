from enum import Enum


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
    def get_tracking_statuses(cls) -> list['OrderStatus']:
        """
        Возвращает статусы, которые отслеживаются в статистике.
        
        Returns:
            list[OrderStatus]: Список статусов для отслеживания
        """
        from ...config.settings import settings
        return [OrderStatus(value) for value in settings.statistics.included_statuses]

    @classmethod
    def get_non_tracking_statuses(cls) -> list['OrderStatus']:
        """
        Возвращает статусы, которые не отслеживаются в статистике.
        
        Returns:
            list[OrderStatus]: Список статусов, не учитываемых в статистике
        """
        from ...config.settings import settings
        return [OrderStatus(value) for value in settings.statistics.excluded_statuses]