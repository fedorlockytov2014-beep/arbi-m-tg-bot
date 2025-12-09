import logging
from datetime import datetime
from typing import Optional

from ...application.dto.incoming_orders import ActivateWarehouseDTO
from ...application.exceptions import (
    InvalidActivationCodeException,
    MaxActivationAttemptsExceededException,
    WarehouseNotFoundException
)
from ...domain.repositories.warehouse_repository import WarehouseRepository

logger = logging.getLogger(__name__)

class ActivateWarehouseUseCase:
    """
    Use case для активации склада.
    
    Отвечает за:
    - Проверку кода активации
    - Привязку склада к Telegram-чату
    - Управление попытками активации
    """
    
    def __init__(
        self,
        warehouse_repository: WarehouseRepository,
    ):
        """
        Инициализирует use case.
        
        Args:
            warehouse_repository: Репозиторий для работы со складами
        """
        self.warehouse_repository = warehouse_repository
        
    async def execute(self, data: ActivateWarehouseDTO) -> bool:
        """
        Выполняет сценарий активации склада.
        
        Args:
            data: DTO с данными для активации склада
            
        Returns:
            bool: True если активация прошла успешно
            
        Raises:
            WarehouseNotFoundException: Если склад не найден
            InvalidActivationCodeException: Если код активации недействителен
            MaxActivationAttemptsExceededException: Если превышено количество попыток
        """
        logger.info(
            "Начало выполнения сценария активации склада",
            extra={
                "warehouse_uid": data.warehouse_uid,
                "chat_id": data.chat_id
            }
        )
        
        # Получение склада по UID
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            logger.error(
                "Склад не найден при попытке активации",
                extra={
                    "warehouse_uid": data.warehouse_uid
                }
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
        
        # Проверка, не активирован ли склад уже
        if warehouse.is_active and warehouse.telegram_chat_id is not None:
            logger.warning(
                "Склад уже активирован",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "current_chat_id": warehouse.telegram_chat_id
                }
            )
            # Если склад уже привязан к этому же чату - возвращаем успех
            if warehouse.telegram_chat_id == data.chat_id:
                return True
            else:
                raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} уже привязан к другому чату")
        
        # Проверка кода активации
        if warehouse.activation_code != data.activation_code:
            logger.warning(
                "Неверный код активации",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "provided_code": data.activation_code,
                    "expected_code": warehouse.activation_code
                }
            )
            raise InvalidActivationCodeException("Неверный код активации")
        
        # Активация склада
        try:
            warehouse.activate(telegram_chat_id=data.chat_id, activation_code=data.activation_code)
            
            # Сохраняем обновленный склад
            await self.warehouse_repository.update(warehouse)
            
            logger.info(
                "Склад успешно активирован",
                extra={
                    "warehouse_uid": warehouse.uid,
                    "chat_id": data.chat_id
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Ошибка при активации склада",
                extra={
                    "warehouse_uid": data.warehouse_uid,
                    "error": str(e),
                    "exc_info": True
                }
            )
            raise