import logging
from datetime import datetime, timedelta
from typing import Optional

from ..entities.order import Order
from ..value_objects.cooking_time import CookingTime
from ..value_objects.order_status import OrderStatus
from ...infrastructure.logging import get_logger, log_server_action, log_error, log_warning

logger = get_logger(__name__)


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
            error_msg = f"Заказ со статусом {order.status} не может быть принят партнёром"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "expected_status": OrderStatus.SENT_TO_PARTNER.value
                }
            )
            raise ValueError(error_msg)

        if accepted_at is None:
            accepted_at = datetime.utcnow()

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.ACCEPTED_BY_PARTNER,
            "accepted_at": accepted_at
        })

        log_server_action(
            logger,
            action="order_accepted_by_partner",
            result="success",
            order_id=updated_order.id,
            warehouse_id=updated_order.warehouse_id,
            accepted_at=accepted_at.isoformat() if accepted_at else None
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
            error_msg = f"Время приготовления можно установить только для заказов в статусе {OrderStatus.ACCEPTED_BY_PARTNER} или {OrderStatus.COOKING}"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "allowed_statuses": [OrderStatus.ACCEPTED_BY_PARTNER.value, OrderStatus.COOKING.value]
                }
            )
            raise ValueError(error_msg)

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

        log_server_action(
            logger,
            action="cooking_time_set",
            result="success",
            order_id=updated_order.id,
            cooking_time_minutes=cooking_time.minutes,
            expected_ready_at=expected_ready_at.isoformat() if expected_ready_at else None
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
            error_msg = f"Заказ со статусом {order.status} не может быть отмечен как готовый к доставке"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "expected_status": OrderStatus.COOKING.value
                }
            )
            raise ValueError(error_msg)

        # Создаём новый объект заказа с обновлённым статусом
        updated_order = order.copy(update={
            "status": OrderStatus.READY_FOR_DELIVERY
        })

        log_server_action(
            logger,
            action="order_marked_as_ready_for_delivery",
            result="success",
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
            error_msg = f"Курьера можно назначить только для заказов со статусом {OrderStatus.READY_FOR_DELIVERY}"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "expected_status": OrderStatus.READY_FOR_DELIVERY.value
                }
            )
            raise ValueError(error_msg)

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.ON_DELIVERY,
            "courier_assigned_at": datetime.utcnow()
        })

        log_server_action(
            logger,
            action="courier_assigned_to_order",
            result="success",
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
            error_msg = f"Заказ можно отметить как доставленный только из статуса {OrderStatus.ON_DELIVERY}"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "expected_status": OrderStatus.ON_DELIVERY.value
                }
            )
            raise ValueError(error_msg)

        # Создаём новый объект заказа с обновлёнными полями
        updated_order = order.copy(update={
            "status": OrderStatus.DELIVERED,
            "delivered_at": datetime.utcnow()
        })

        log_server_action(
            logger,
            action="order_marked_as_delivered",
            result="success",
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
            error_msg = f"Заказ со статусом {order.status} не может быть отменён"
            log_error(
                logger,
                ValueError(error_msg),
                context={
                    "order_id": order.id,
                    "current_status": order.status.value,
                    "forbidden_statuses": [OrderStatus.DELIVERED.value, OrderStatus.CANCELLED.value]
                }
            )
            raise ValueError(error_msg)

        # Создаём новый объект заказа с обновлённым статусом
        updated_order = order.copy(update={
            "status": OrderStatus.CANCELLED
        })

        log_server_action(
            logger,
            action="order_cancelled",
            result="success",
            order_id=updated_order.id,
            previous_status=order.status.value
        )

        return updated_order