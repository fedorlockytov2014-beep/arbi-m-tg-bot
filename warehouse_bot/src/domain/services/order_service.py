import logging
from datetime import datetime, timedelta
from typing import Optional

from ..entities.order import Order
from ..value_objects.cooking_time import CookingTime
from ..value_objects.order_status import OrderStatus

logger = logging.getLogger(__name__)


class OrderService:
    """
    Доменный сервис для бизнес-логики заказов.
    
    Отвечает за:
    - Изменение статусов заказов
    - Расчет времени готовности
    - Проверку валидности переходов статусов
    """

    def __init__(self):
        """
        Инициализирует сервис заказов.
        """
        pass

    def can_transition_status(self, from_status: OrderStatus, to_status: OrderStatus) -> bool:
        """
        Проверяет, возможен ли переход из одного статуса в другой.
        
        Args:
            from_status: Текущий статус
            to_status: Целевой статус
            
        Returns:
            bool: True если переход возможен, иначе False
        """
        valid_transitions = {
            OrderStatus.NEW: [OrderStatus.SENT_TO_PARTNER],
            OrderStatus.SENT_TO_PARTNER: [OrderStatus.ACCEPTED_BY_PARTNER, OrderStatus.CANCELLED],
            OrderStatus.ACCEPTED_BY_PARTNER: [OrderStatus.COOKING, OrderStatus.CANCELLED],
            OrderStatus.COOKING: [OrderStatus.READY_FOR_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.READY_FOR_DELIVERY: [OrderStatus.ON_DELIVERY, OrderStatus.CANCELLED],
            OrderStatus.ON_DELIVERY: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [],
            OrderStatus.CANCELLED: []
        }

        return to_status in valid_transitions.get(from_status, [])

    async def accept_order(self, order: Order, accepted_at: Optional[datetime] = None) -> Order:
        """
        Принимает заказ партнёром.
        
        Args:
            order: Заказ для принятия
            accepted_at: Время принятия (по умолчанию текущее)
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ уже принят или статус не позволяет принятие
        """
        if order.status != OrderStatus.SENT_TO_PARTNER:
            raise ValueError(f"Заказ со статусом {order.status} не может быть принят партнёром")

        if accepted_at is None:
            accepted_at = datetime.utcnow()

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.ACCEPTED_BY_PARTNER,
            "accepted_at": accepted_at
        })

        logger.info(
            "Заказ принят партнёром",
            order_id=updated_order.id,
            warehouse_id=updated_order.warehouse_id,
            accepted_at=accepted_at
        )

        return updated_order

    async def set_cooking_time(
        self,
        order: Order,
        cooking_time: CookingTime,
        expected_ready_at: Optional[datetime] = None
    ) -> Order:
        """
        Устанавливает время приготовления заказа.
        
        Args:
            order: Заказ для обновления
            cooking_time: Время приготовления
            expected_ready_at: Ожидаемое время готовности (по умолчанию текущее + время приготовления)
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ не в подходящем статусе
        """
        if order.status not in [OrderStatus.ACCEPTED_BY_PARTNER, OrderStatus.COOKING]:
            raise ValueError(f"Время приготовления можно установить только для заказов в статусе {OrderStatus.ACCEPTED_BY_PARTNER} или {OrderStatus.COOKING}")

        if expected_ready_at is None:
            if order.accepted_at:
                expected_ready_at = order.accepted_at + timedelta(minutes=cooking_time.minutes)
            else:
                expected_ready_at = datetime.utcnow() + timedelta(minutes=cooking_time.minutes)

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.COOKING,
            "cooking_time_minutes": cooking_time.minutes,
            "expected_ready_at": expected_ready_at
        })

        logger.info(
            "Установлено время приготовления заказа",
            order_id=updated_order.id,
            cooking_time_minutes=cooking_time.minutes,
            expected_ready_at=expected_ready_at
        )

        return updated_order

    async def mark_as_ready_for_delivery(self, order: Order) -> Order:
        """
        Отмечает заказ как готовый к доставке.
        
        Args:
            order: Заказ для обновления
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ не в подходящем статусе
        """
        if order.status != OrderStatus.COOKING:
            raise ValueError(f"Заказ со статусом {order.status} не может быть отмечен как готовый к доставке")

        # Создаём новый объект заказа с обновлённым статусом
        updated_order = order.copy(update={
            "status": OrderStatus.READY_FOR_DELIVERY
        })

        logger.info(
            "Заказ отмечен как готовый к доставке",
            order_id=updated_order.id
        )

        return updated_order

    async def assign_courier(self, order: Order) -> Order:
        """
        Назначает курьера для заказа.
        
        Args:
            order: Заказ для обновления
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ не в подходящем статусе
        """
        if order.status != OrderStatus.READY_FOR_DELIVERY:
            raise ValueError(f"Курьера можно назначить только для заказов со статусом {OrderStatus.READY_FOR_DELIVERY}")

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.ON_DELIVERY,
            "courier_assigned_at": datetime.utcnow()
        })

        logger.info(
            "Курьер назначен для заказа",
            order_id=updated_order.id
        )

        return updated_order

    async def mark_as_delivered(self, order: Order) -> Order:
        """
        Отмечает заказ как доставленный.
        
        Args:
            order: Заказ для обновления
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ не в подходящем статусе
        """
        if order.status != OrderStatus.ON_DELIVERY:
            raise ValueError(f"Заказ можно отметить как доставленный только из статуса {OrderStatus.ON_DELIVERY}")

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.DELIVERED,
            "delivered_at": datetime.utcnow()
        })

        logger.info(
            "Заказ отмечен как доставленный",
            order_id=updated_order.id
        )

        return updated_order

    async def cancel_order(self, order: Order) -> Order:
        """
        Отменяет заказ.
        
        Args:
            order: Заказ для отмены
            
        Returns:
            Order: Обновлённый заказ
            
        Raises:
            ValueError: Если заказ уже доставлен или отменён
        """
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            raise ValueError(f"Заказ со статусом {order.status} не может быть отменён")

        # Создаём новый объект заказа с обновлённым статусом
        updated_order = order.copy(update={
            "status": OrderStatus.CANCELLED
        })

        logger.info(
            "Заказ отменён",
            order_id=updated_order.id,
            previous_status=order.status
        )

        return updated_order