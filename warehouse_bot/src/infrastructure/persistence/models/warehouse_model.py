from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class WarehouseModel(Base):
    """
    Database model for warehouses.
    """
    __tablename__ = "warehouses"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    telegram_chat_id = Column(Integer, nullable=True)  # Nullable since not all warehouses are attached to chats
    activated_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    activation_code = Column(String, nullable=True)
    max_orders_per_day = Column(Integer, default=100)
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())