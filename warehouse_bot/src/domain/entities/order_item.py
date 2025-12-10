from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ..value_objects.money import Money


class OrderItem(BaseModel):
    """
    Представляет элемент заказа (товар).
    
    Attributes:
        id: Уникальный идентификатор элемента заказа
        name: Название товара
        quantity: Количество товара
        price: Цена за единицу товара
        total_price: Общая цена (количество * цена за единицу)
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    price: Money
    
    def calculate_total_price(self) -> Money:
        """
        Рассчитывает общую стоимость товара (количество * цена).
        
        Returns:
            Money: Общая стоимость товара
        """
        total_amount = self.price.amount * self.quantity
        return Money(amount=total_amount)
    
    @property
    def total_price(self) -> Money:
        """
        Общая цена товара (количество * цена за единицу).
        
        Returns:
            Money: Общая цена
        """
        return self.calculate_total_price()

    class Config:
        json_encoders = {
            UUID: lambda v: str(v),
        }