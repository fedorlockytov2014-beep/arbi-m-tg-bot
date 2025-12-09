import logging
from dataclasses import dataclass
from typing import Optional

from src.application.exceptions import WarehouseNotFoundException
from src.domain.entities.warehouse import Warehouse
from src.domain.repositories.warehouse_repository import WarehouseRepository

logger = logging.getLogger(__name__)


@dataclass
class ActivateWarehouseDTO:
    """DTO для активации склада по коду"""
    chat_id: int
    activation_code: str


@dataclass
class ActivateWarehouseByUidDTO:
    """DTO для активации склада по UID (deep-linking)"""
    chat_id: int
    warehouse_uid: str


class ActivateWarehouseUseCase:
    """
    Use case для активации склада.
    
    Отвечает за:
    - Проверку кода активации
    - Привязку чата к складу
    - Проверку, активирован ли уже склад для чата
    """
    
    def __init__(self, warehouse_repository: WarehouseRepository):
        self.warehouse_repository = warehouse_repository
    
    async def execute(self, dto: ActivateWarehouseDTO) -> Warehouse:
        """
        Активирует склад по коду.
        
        Args:
            dto: Данные для активации
            
        Returns:
            Warehouse: Активированный склад
            
        Raises:
            WarehouseNotFoundException: Если код неверный или склад уже привязан
        """
        logger.info(
            "Начало активации склада по коду",
            chat_id=dto.chat_id,
            activation_code=dto.activation_code
        )
        
        # Найти склад по коду активации
        warehouse = await self.warehouse_repository.get_by_activation_code(dto.activation_code)
        if not warehouse:
            logger.warning(
                "Неверный код активации",
                chat_id=dto.chat_id,
                activation_code=dto.activation_code
            )
            raise WarehouseNotFoundException("Неверный код активации")
        
        # Проверить, не привязан ли склад уже к другому чату
        if warehouse.telegram_chat_id is not None:
            logger.warning(
                "Склад уже привязан к другому чату",
                warehouse_uid=warehouse.uid,
                existing_chat_id=warehouse.telegram_chat_id,
                new_chat_id=dto.chat_id
            )
            raise WarehouseNotFoundException("Склад уже привязан к другому чату")
        
        # Привязать склад к чату
        warehouse.telegram_chat_id = dto.chat_id
        updated_warehouse = await self.warehouse_repository.update(warehouse)
        
        logger.info(
            "Склад успешно активирован",
            warehouse_uid=warehouse.uid,
            chat_id=dto.chat_id
        )
        
        return updated_warehouse
    
    async def execute_by_uid(self, dto: ActivateWarehouseByUidDTO) -> Warehouse:
        """
        Активирует склад по UID (для deep-linking).
        
        Args:
            dto: Данные для активации по UID
            
        Returns:
            Warehouse: Активированный склад
            
        Raises:
            WarehouseNotFoundException: Если склад не найден или уже привязан
        """
        logger.info(
            "Начало активации склада по UID",
            chat_id=dto.chat_id,
            warehouse_uid=dto.warehouse_uid
        )
        
        # Найти склад по UID
        warehouse = await self.warehouse_repository.get_by_uid(dto.warehouse_uid)
        if not warehouse:
            logger.warning(
                "Склад с указанным UID не найден",
                warehouse_uid=dto.warehouse_uid,
                chat_id=dto.chat_id
            )
            raise WarehouseNotFoundException("Склад не найден")
        
        # Проверить, не привязан ли склад уже к другому чату
        if warehouse.telegram_chat_id is not None:
            logger.warning(
                "Склад уже привязан к другому чату",
                warehouse_uid=warehouse.uid,
                existing_chat_id=warehouse.telegram_chat_id,
                new_chat_id=dto.chat_id
            )
            raise WarehouseNotFoundException("Склад уже привязан к другому чату")
        
        # Привязать склад к чату
        warehouse.telegram_chat_id = dto.chat_id
        updated_warehouse = await self.warehouse_repository.update(warehouse)
        
        logger.info(
            "Склад успешно активирован по UID",
            warehouse_uid=warehouse.uid,
            chat_id=dto.chat_id
        )
        
        return updated_warehouse
    
    async def is_chat_activated(self, chat_id: int) -> bool:
        """
        Проверяет, активирован ли склад для указанного чата.
        
        Args:
            chat_id: ID чата
            
        Returns:
            bool: True если склад активирован
        """
        warehouse = await self.warehouse_repository.get_by_chat_id(chat_id)
        return warehouse is not None