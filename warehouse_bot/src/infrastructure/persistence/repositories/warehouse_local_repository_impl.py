from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine, select, update, delete, and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from ....domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ....domain.entities.warehouse import Warehouse
from ...logging import get_logger
from ..models import WarehouseModel

logger = get_logger(__name__)


class WarehouseLocalRepositoryImpl(IWarehouseDBRepository):
    """
    Локальная реализация репозитория складов с использованием SQLite.
    """
    
    def __init__(self, db_path: str = "sqlite:///./warehouse_local.db"):
        """
        Инициализирует репозиторий с локальной SQLite базой данных.
        
        Args:
            db_path: Путь к SQLite базе данных
        """
        self.engine = create_engine(db_path, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        # Создаем таблицы при инициализации
        from ..models import Base
        Base.metadata.create_all(bind=self.engine)
    
    def _map_to_entity(self, model: WarehouseModel) -> Warehouse:
        """Преобразует модель базы данных в доменную сущность."""
        return Warehouse(
            id=model.id,
            name=model.name,
            address=model.address,
            telegram_chat_id=model.telegram_chat_id,
            activated_at=model.activated_at,
            deactivated_at=model.deactivated_at,
            is_active=model.is_active,
            activation_code=model.activation_code,
            max_orders_per_day=model.max_orders_per_day,
            timezone=model.timezone
        )
    
    def _map_to_model(self, entity: Warehouse) -> WarehouseModel:
        """Преобразует доменную сущность в модель базы данных."""
        return WarehouseModel(
            id=entity.id,
            name=entity.name,
            address=entity.address,
            telegram_chat_id=entity.telegram_chat_id,
            activated_at=entity.activated_at,
            deactivated_at=entity.deactivated_at,
            is_active=entity.is_active,
            activation_code=entity.activation_code,
            max_orders_per_day=entity.max_orders_per_day,
            timezone=entity.timezone
        )
    
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """
        Получает склад по ID.
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(WarehouseModel).where(WarehouseModel.id == warehouse_id)
                result = session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    return self._map_to_entity(model)
        except SQLAlchemyError as e:
            await logger.error(f"Database error while getting warehouse by ID {warehouse_id}: {e}")
        except Exception as e:
            await logger.error(f"Unexpected error while getting warehouse by ID {warehouse_id}: {e}")
        
        return None

    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID Telegram-чата.
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(WarehouseModel).where(WarehouseModel.telegram_chat_id == chat_id)
                result = session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    return self._map_to_entity(model)
        except SQLAlchemyError as e:
            await logger.error(f"Database error while getting warehouse by chat ID {chat_id}: {e}")
        except Exception as e:
            await logger.error(f"Unexpected error while getting warehouse by chat ID {chat_id}: {e}")
        
        return None

    async def get_all(self) -> List[Warehouse]:
        """
        Получает все склады.
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(WarehouseModel)
                result = session.execute(stmt)
                models = result.scalars().all()
                
                return [self._map_to_entity(model) for model in models]
        except SQLAlchemyError as e:
            await logger.error(f"Database error while getting all warehouses: {e}")
        except Exception as e:
            await logger.error(f"Unexpected error while getting all warehouses: {e}")
        
        return []

    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохраняет склад.
        """
        try:
            with self.SessionLocal() as session:
                model = self._map_to_model(warehouse)
                session.add(model)
                session.commit()
                session.refresh(model)
                
                return self._map_to_entity(model)
        except SQLAlchemyError as e:
            await logger.error(f"Database error while saving warehouse {warehouse.id}: {e}")
            raise
        except Exception as e:
            await logger.error(f"Unexpected error while saving warehouse {warehouse.id}: {e}")
            raise

    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет склад.
        """
        try:
            with self.SessionLocal() as session:
                stmt = (
                    update(WarehouseModel)
                    .where(WarehouseModel.id == warehouse.id)
                    .values(
                        name=warehouse.name,
                        address=warehouse.address,
                        telegram_chat_id=warehouse.telegram_chat_id,
                        activated_at=warehouse.activated_at,
                        deactivated_at=warehouse.deactivated_at,
                        is_active=warehouse.is_active,
                        activation_code=warehouse.activation_code,
                        max_orders_per_day=warehouse.max_orders_per_day,
                        timezone=warehouse.timezone
                    )
                )
                session.execute(stmt)
                session.commit()
                
                # Get updated record
                stmt = select(WarehouseModel).where(WarehouseModel.id == warehouse.id)
                result = session.execute(stmt)
                updated_model = result.scalar_one()
                
                return self._map_to_entity(updated_model)
        except SQLAlchemyError as e:
            await logger.error(f"Database error while updating warehouse {warehouse.id}: {e}")
            raise
        except Exception as e:
            await logger.error(f"Unexpected error while updating warehouse {warehouse.id}: {e}")
            raise

    async def delete(self, warehouse_id: str) -> bool:
        """
        Удаляет склад.
        """
        try:
            with self.SessionLocal() as session:
                stmt = delete(WarehouseModel).where(WarehouseModel.id == warehouse_id)
                result = session.execute(stmt)
                session.commit()
                
                return result.rowcount > 0
        except SQLAlchemyError as e:
            await logger.error(f"Database error while deleting warehouse {warehouse_id}: {e}")
        except Exception as e:
            await logger.error(f"Unexpected error while deleting warehouse {warehouse_id}: {e}")
        
        return False

    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации.
        """
        try:
            with self.SessionLocal() as session:
                stmt = select(WarehouseModel).where(
                    and_(
                        WarehouseModel.activation_code == activation_code,
                        WarehouseModel.is_active == False  # Only inactive warehouses can be found by activation code
                    )
                )
                result = session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if model:
                    return self._map_to_entity(model)
        except SQLAlchemyError as e:
            await logger.error(f"Database error while finding warehouse by activation code {activation_code}: {e}")
        except Exception as e:
            await logger.error(f"Unexpected error while finding warehouse by activation code {activation_code}: {e}")
        
        return None

    async def deactivate_by_telegram_chat_id(self, chat_id: int) -> bool:
        """
        Деактивирует склад по ID Telegram-чата.
        """
        try:
            with self.SessionLocal() as session:
                # Находим склад по ID чата
                stmt = select(WarehouseModel).where(WarehouseModel.telegram_chat_id == chat_id)
                result = session.execute(stmt)
                model = result.scalar_one_or_none()
                
                if not model:
                    await logger.info(f"No warehouse found with chat ID {chat_id} to deactivate")
                    return False
                
                # Обновляем поля для деактивации
                update_stmt = (
                    update(WarehouseModel)
                    .where(WarehouseModel.id == model.id)
                    .values(
                        is_active=False,
                        deactivated_at=datetime.utcnow(),
                        telegram_chat_id=None  # Remove chat association
                    )
                )
                session.execute(update_stmt)
                session.commit()
                
                await logger.info(f"Warehouse {model.id} deactivated successfully")
                return True
        except SQLAlchemyError as e:
            await logger.error(f"Database error while deactivating warehouse by chat ID {chat_id}: {e}")
            return False
        except Exception as e:
            await logger.error(f"Unexpected error while deactivating warehouse by chat ID {chat_id}: {e}")
            return False