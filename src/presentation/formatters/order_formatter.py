def format_new_order_message(order_data: dict) -> str:
    """
    Форматирует сообщение о новом заказе для отправки в Telegram.
    
    Args:
        order_data: Данные заказа из CRM
        
    Returns:
        str: Отформатированное сообщение о заказе
    """
    order_id = order_data.get("id", "N/A")
    customer_name = order_data.get("customer_name", "N/A")
    customer_phone = order_data.get("customer_phone", "N/A")
    delivery_address = order_data.get("delivery_address", "N/A")
    total_amount = order_data.get("total_amount", "N/A")
    comment = order_data.get("comment", "")
    items = order_data.get("items", [])
    
    message = f"📦 <b>Новый заказ #{order_id}</b>\n\n"
    message += f"👤 <b>Клиент:</b> {customer_name}\n"
    message += f"📱 <b>Телефон:</b> {customer_phone}\n"
    message += f"📍 <b>Адрес доставки:</b> {delivery_address}\n"
    message += f"💰 <b>Сумма заказа:</b> {total_amount} руб.\n"
    
    if comment:
        message += f"📝 <b>Комментарий:</b> {comment}\n\n"
    else:
        message += "\n"
    
    message += "<b>Состав заказа:</b>\n"
    for item in items:
        name = item.get("name", "N/A")
        quantity = item.get("quantity", 0)
        price = item.get("price", 0)
        message += f"  • {name} x{quantity} - {price} руб.\n"
    
    return message


def format_order_status_message(order_id: str, status: str, cooking_time: int = None, expected_ready_at: str = None) -> str:
    """
    Форматирует сообщение об изменении статуса заказа.
    
    Args:
        order_id: ID заказа
        status: Новый статус заказа
        cooking_time: Время приготовления в минутах
        expected_ready_at: Ожидаемое время готовности
        
    Returns:
        str: Отформатированное сообщение
    """
    status_messages = {
        "new": "Заказ принят",
        "sent_to_partner": "Заказ отправлен партнеру",
        "accepted_by_partner": "Заказ принят партнёром",
        "cooking": "Заказ в процессе приготовления",
        "ready_for_delivery": "Заказ готов к доставке",
        "on_delivery": "Заказ в пути",
        "delivered": "Заказ доставлен",
        "cancelled": "Заказ отменён"
    }
    
    status_text = status_messages.get(status, status)
    
    message = f"🔄 <b>Статус заказа #{order_id}</b>\n"
    message += f"🔹 <b>Новый статус:</b> {status_text}\n"
    
    if cooking_time is not None:
        message += f"⏱ <b>Время приготовления:</b> {cooking_time} мин\n"
    
    if expected_ready_at is not None:
        message += f"⏰ <b>Ожидаемое время готовности:</b> {expected_ready_at}\n"
    
    return message


def format_cooking_time_confirmation(cooking_time: int, expected_ready_at: str) -> str:
    """
    Форматирует сообщение о подтверждении времени готовки.
    
    Args:
        cooking_time: Время приготовления в минутах
        expected_ready_at: Ожидаемое время готовности
        
    Returns:
        str: Отформатированное сообщение
    """
    return (
        f"⏱ <b>Время готовности:</b> {cooking_time} мин "
        f"(до {expected_ready_at})"
    )


def format_order_ready_confirmation(order_id: str) -> str:
    """
    Форматирует сообщение о готовности заказа к доставке.
    
    Args:
        order_id: ID заказа
        
    Returns:
        str: Отформатированное сообщение
    """
    return (
        f"✅ <b>Заказ #{order_id} готов к доставке.</b>\n"
        f"Курьер будет направлен."
    )