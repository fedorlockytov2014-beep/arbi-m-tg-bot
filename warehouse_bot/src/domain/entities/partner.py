from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Partner(BaseModel):
    """
    Представляет партнёра (владельца склада/магазина).
    
    Attributes:
        id: Уникальный идентификатор партнёра
        name: Имя партнёра
        company_name: Название компании партнёра
        email: Email партнёра
        phone: Телефон партнёра
        created_at: Время создания аккаунта партнёра
        updated_at: Время последнего обновления аккаунта
        is_active: Статус активности партнёра
        warehouses: Список ID складов, принадлежащих партнёру
    """
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=1, max_length=20)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    warehouses: List[str] = []

    def add_warehouse(self, warehouse_id: str) -> None:
        """
        Добавляет склад к партнёру.
        
        Args:
            warehouse_id: ID склада для добавления
        """
        if warehouse_id not in self.warehouses:
            self.warehouses.append(warehouse_id)
            self.updated_at = datetime.utcnow()

    def remove_warehouse(self, warehouse_id: str) -> None:
        """
        Удаляет склад у партнёра.
        
        Args:
            warehouse_id: ID склада для удаления
        """
        if warehouse_id in self.warehouses:
            self.warehouses.remove(warehouse_id)
            self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Деактивирует аккаунт партнёра.
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """
        Активирует аккаунт партнёра.
        """
        self.is_active = True
        self.updated_at = datetime.utcnow()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }