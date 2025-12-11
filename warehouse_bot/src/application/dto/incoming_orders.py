from typing import List, Optional

from pydantic import BaseModel, Field

from ...domain.value_objects.order_status import OrderStatus


class AcceptOrderDTO(BaseModel):
    """
    DTO для принятия заказа партнёром.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
    """
    order_id: str
    warehouse_id: str
    chat_id: int


class SetCookingTimeDTO(BaseModel):
    """
    DTO для установки времени приготовления.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
        cooking_time_minutes: Время приготовления в минутах
    """
    order_id: str
    warehouse_id: str
    chat_id: int
    cooking_time_minutes: int = Field(..., gt=0, le=180)


class UpdateOrderStatusDTO(BaseModel):
    """
    DTO для обновления статуса заказа.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
        status: Новый статус заказа
    """
    order_id: str
    warehouse_id: str
    chat_id: int
    status: OrderStatus


class AddOrderPhotoDTO(BaseModel):
    """
    DTO для добавления фотографии к заказу.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
        photo_url: URL фотографии
    """
    order_id: str
    warehouse_id: str
    chat_id: int
    photo_url: str


class GetOrderDetailsDTO(BaseModel):
    """
    DTO для получения деталей заказа.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
    """
    order_id: str
    warehouse_id: str
    chat_id: int


class ActivateWarehouseDTO(BaseModel):
    """
    DTO для активации склада.
    
    Attributes:
        warehouse_id: ID склада
        activation_code: Код активации
        chat_id: ID Telegram-чата
    """
    warehouse_id: str
    activation_code: str
    chat_id: int


class CreateOrderDTO(BaseModel):
    """
    DTO для создания заказа.
    
    Attributes:
        order_number: Номер заказа
        warehouse_id: ID склада
        customer_name: Имя клиента
        customer_phone: Телефон клиента
        delivery_address: Адрес доставки
        items: Список товаров
        total_amount: Общая сумма
        comment: Комментарий
        payment_type: Тип оплаты
    """
    order_number: str
    warehouse_id: str
    customer_name: str
    customer_phone: str
    delivery_address: str
    items: List[dict]  # Will be converted to OrderItem
    total_amount: float
    comment: Optional[str] = None
    payment_type: str = "cash"


class OrderItemDTO(BaseModel):
    """
    DTO для товара в заказе.
    
    Attributes:
        name: Название товара
        quantity: Количество
        price: Цена за единицу
    """
    name: str
    quantity: int
    price: float


class CancelOrderDTO(BaseModel):
    """
    DTO для отмены заказа.
    
    Attributes:
        order_id: ID заказа
        warehouse_id: ID склада
        chat_id: ID Telegram-чата
    """
    order_id: str
    warehouse_id: str
    chat_id: int