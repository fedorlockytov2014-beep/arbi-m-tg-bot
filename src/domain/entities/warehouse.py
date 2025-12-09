from dataclasses import dataclass
from typing import Optional


@dataclass
class Warehouse:
    """
    Сущность склада.
    
    Attributes:
        uid: Уникальный идентификатор склада
        name: Название склада
        address: Адрес склада
        telegram_chat_id: ID Telegram чата, привязанного к складу
    """
    uid: str
    name: str
    address: str
    telegram_chat_id: Optional[int] = None