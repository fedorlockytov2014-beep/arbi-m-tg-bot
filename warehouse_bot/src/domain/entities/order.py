from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from warehouse_bot.config.settings import settings
from ..value_objects.order_status import OrderStatus
from ..value_objects.money import Money


class OrderItem(BaseModel):
    """
    Представляет элемент заказа (товар).
    
    Attributes:
        id: Уникальный идентификатор элемента заказа
        name: Название товара
        quantity: Количество товара
        price: Цена за единицу товара
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    price: Money


class Order(BaseModel):
    """
    Представляет заказ от клиента.
    
    Attributes:
        id: Уникальный идентификатор заказа
        order_number: Номер заказа (генерируется системой)
        warehouse_id: ID склада/магазина, которому предназначен заказ
        created_at: Время создания заказа
        customer_name: Имя клиента
        customer_phone: Телефон клиента
        delivery_address: Адрес доставки
        items: Список товаров в заказе
        total_amount: Общая сумма заказа
        comment: Комментарий к заказу
        payment_type: Тип оплаты
        status: Текущий статус заказа
        accepted_at: Время принятия заказа партнёром
        cooking_time_minutes: Время приготовления в минутах
        expected_ready_at: Ожидаемое время готовности
        courier_assigned_at: Время назначения курьера
        delivered_at: Время доставки
        photos: Ссылки на фотографии заказа
    """
    id: UUID = Field(default_factory=uuid4)
    order_number: str
    warehouse_id: str
    created_at: datetime
    customer_name: str
    customer_phone: str
    delivery_address: str
    items: List[OrderItem]
    total_amount: Money
    comment: Optional[str] = None
    payment_type: str
    status: OrderStatus = OrderStatus.NEW
    accepted_at: Optional[datetime] = None
    cooking_time_minutes: Optional[int] = None
    expected_ready_at: Optional[datetime] = None
    courier_assigned_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    photos: List[str] = []

    def calculate_total_amount(self) -> Money:
        """
        Рассчитывает общую сумму заказа на основе товаров.
        
        Returns:
            Money: Общая сумма заказа
        """
        total = sum((item.price.amount * item.quantity for item in self.items), 0)
        return Money(amount=total)

    def add_photo(self, photo_url: str) -> None:
        """
        Добавляет фото к заказу.
        
        Args:
            photo_url: URL фотографии
            
        Raises:
            ValueError: Если достигнуто максимальное количество фотографий
        """

        if len(self.photos) >= settings.security.max_photos_per_order:
            raise ValueError(f"Maximum number of photos per order is {settings.security.max_photos_per_order}")
        self.photos.append(photo_url)

    def update_status(self, new_status: OrderStatus) -> None:
        """
        Обновляет статус заказа.
        
        Args:
            new_status: Новый статус заказа
        """
        self.status = new_status

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }