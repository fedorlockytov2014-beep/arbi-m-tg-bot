from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from warehouse_bot.config.settings import settings
from ..value_objects.order_status import OrderStatus
from ..value_objects.money import Money
from .order_item import OrderItem


class Order(BaseModel):
    """
    Представляет заказ от клиента.
    
    Attributes:
        id: Уникальный идентификатор заказа
        # order_number: Номер заказа (генерируется системой)
        warehouse_address: адрес склада/магазина, которому предназначен заказ
        created_at: Время создания заказа
        # customer_name: Имя клиента
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
    id: int
    warehouse_address: str
    created_at: datetime
    customer_phone: Optional[str] = ""
    customer_name: Optional[str] = ""
    delivery_address: str
    delivery_price: Optional[str | int | float | Decimal] = None
    items: List[OrderItem]
    total_amount: Money
    comment: Optional[str] = ""
    payment_type: str
    payment_info: Optional[str] = ""
    status: OrderStatus = OrderStatus.WAIT_FOR_ASSEMBLY
    accepted_at: Optional[datetime] = None
    cooking_time_minutes: Optional[int] = None
    expected_ready_at: Optional[datetime] = None
    courier_assigned_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    photos: List[str] = []
    what_to_do: Optional[str] = None

    def calculate_total_amount(self) -> Money:
        """
        Рассчитывает общую сумму заказа на основе товаров.
        
        Returns:
            Money: Общая сумма заказа
        """
        total = Decimal(sum((item.price.amount * item.count for item in self.items), 0))
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