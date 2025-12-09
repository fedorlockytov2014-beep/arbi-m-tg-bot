from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AcceptOrderDTO:
    """DTO для принятия заказа"""
    order_id: str
    chat_id: int
    warehouse_uid: str


@dataclass
class SetCookingTimeDTO:
    """DTO для установки времени готовки"""
    order_id: str
    chat_id: int
    cooking_time_minutes: int


@dataclass
class ConfirmReadyDTO:
    """DTO для подтверждения готовности заказа"""
    order_id: str
    chat_id: int
    photo_file_ids: List[str]