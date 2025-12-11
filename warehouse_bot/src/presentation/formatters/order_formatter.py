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
        f" • {item.name} ×{item.count} — {item.price.amount} ₽"
        for item in order.items
    ])

    message = (
        "🛒 <b>Новый заказ!</b>\n\n"
        f"🆔 <b>Заказ №{order.id}</b>\n"
        f"🧑‍💼 <b>Клиент:</b> {order.customer_name or "<i>нет</i>"}\n" 
        f"📞 <b>Телефон:</b> {order.customer_phone or "<i>нет</i>"}\n\n"
        f"🏠 <b>Адрес:</b> {order.delivery_address or "<i>нет</i>"}\n\n"
        f"📝 <b>Комментарий:</b> {order.comment or '<i>нет</i>'}\n\n"
        f"📋 <b>Состав заказа:</b>\n{items_text}\n\n"
        f"🚚 <b>Стоимость доставки:</b> {order.delivery_price} ₽\n\n"
        f"💰 <b>Итого:</b> {order.total_amount.amount} ₽\n"
        f"🕒 <b>Время создания:</b> {order.created_at.strftime('%H:%M') if order.created_at else '<i>не указано</i>'}"
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