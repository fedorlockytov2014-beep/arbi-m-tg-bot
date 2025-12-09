from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Warehouse(BaseModel):
    """
    Представляет склад/магазин партнёра.
    
    Attributes:
        id: Уникальный идентификатор склада
        uid: Уникальный идентификатор склада (публичный)
        name: Название склада/магазина
        address: Адрес склада/магазина
        phone: Контактный телефон
        telegram_chat_id: ID Telegram-чата, привязанного к складу
        activated_at: Время активации склада
        deactivated_at: Время деактивации склада (если деактивирован)
        is_active: Статус активности склада
        activation_code: Код активации склада (временный)
        max_orders_per_day: Максимальное количество заказов в день
        timezone: Часовой пояс склада
    """
    id: UUID = Field(default_factory=uuid4)
    uid: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=1, max_length=500)
    phone: str = Field(..., min_length=1, max_length=20)
    telegram_chat_id: Optional[int] = None
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    is_active: bool = False
    activation_code: Optional[str] = None
    max_orders_per_day: int = 100
    timezone: str = "UTC"

    def activate(self, telegram_chat_id: int, activation_code: str) -> None:
        """
        Активирует склад и привязывает к Telegram-чату.
        
        Args:
            telegram_chat_id: ID Telegram-чата
            activation_code: Код активации
        """
        self.telegram_chat_id = telegram_chat_id
        self.activation_code = activation_code
        self.is_active = True
        self.activated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Деактивирует склад.
        """
        self.is_active = False
        self.deactivated_at = datetime.utcnow()
        self.telegram_chat_id = None

    def can_accept_orders(self) -> bool:
        """
        Проверяет, может ли склад принимать заказы.
        
        Returns:
            bool: True если склад активен и может принимать заказы
        """
        return self.is_active and self.telegram_chat_id is not None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }