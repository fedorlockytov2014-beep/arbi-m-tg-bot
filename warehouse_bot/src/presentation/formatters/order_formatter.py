from typing import Dict, Any
from ...domain.entities.order import Order


def format_order_message(order: Order) -> str:
    """
    Форматирует сообщение с информацией о заказе.
    
    Args:
        order: Объект заказа
        
    Returns:
        str: Отформатированное сообщение о заказе
    """
    items_text = "\n".join([
        f" • {item.name} ×{item.quantity} — {item.price.amount} ₽"
        for item in order.items
    ])
    
    message = (
        f"🆕 Новый заказ №{order.order_number}\n"
        f" Клиент: {order.customer_name}\n"
        f" Телефон: {order.customer_phone}\n"
        f" Адрес: {order.delivery_address}\n"
        f" Комментарий: {order.comment or 'Нет'}\n"
        f"\nСостав:\n{items_text}\n"
        f"\nИтог: {order.total_amount.amount} ₽\n"
        f" Время создания: {order.created_at.strftime('%H:%M') if order.created_at else 'N/A'}"
    )
    
    return message


def format_order_status_message(order: Order) -> str:
    """
    Форматирует сообщение с информацией о статусе заказа.
    
    Args:
        order: Объект заказа
        
    Returns:
        str: Отформатированное сообщение о статусе заказа
    """
    status_text = {
        "new": "новый",
        "sent_to_partner": "отправлен партнеру",
        "accepted_by_partner": "принят партнером",
        "cooking": "готовится",
        "ready_for_delivery": "готов к доставке",
        "on_delivery": "в доставке",
        "delivered": "доставлен",
        "cancelled": "отменен"
    }.get(order.status.value, order.status.value)
    
    message = f"Заказ №{order.order_number} - статус: {status_text}"
    
    if order.cooking_time_minutes:
        message += f"\nВремя готовки: {order.cooking_time_minutes} мин"
    
    if order.expected_ready_at:
        message += f"\nОжидаемое время готовности: {order.expected_ready_at.strftime('%H:%M')}"
    
    return message