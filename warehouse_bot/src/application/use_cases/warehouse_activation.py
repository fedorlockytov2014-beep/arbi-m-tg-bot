from ...application.dto.incoming_orders import ActivateWarehouseDTO
from ...application.exceptions import (
    InvalidActivationCodeException,
    WarehouseNotFoundException
)
from ...domain.repositories.warehouse_repository import WarehouseRepository
from ...infrastructure.logging import get_logger, log_user_action, log_server_action, log_error, log_warning

logger = get_logger(__name__)

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
        await log_user_action(
            logger,
            user_id=data.chat_id,
            action="warehouse_activation_attempt",
            chat_id=data.chat_id,
            warehouse_uid=data.warehouse_uid
        )
        
        # Получение склада по UID
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            await log_error(
                logger,
                WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден"),
                context={
                    "warehouse_uid": data.warehouse_uid,
                    "chat_id": data.chat_id
                }
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
        
        # Проверка, не активирован ли склад уже
        if warehouse.is_active and warehouse.telegram_chat_id is not None:
            await log_warning(
                logger,
                "Склад уже активирован",
                warehouse_uid=data.warehouse_uid,
                current_chat_id=warehouse.telegram_chat_id,
                attempted_chat_id=data.chat_id
            )
            # Если склад уже привязан к этому же чату - возвращаем успех
            if warehouse.telegram_chat_id == data.chat_id:
                await log_server_action(
                    logger,
                    action="warehouse_already_activated_same_chat",
                    result="success",
                    warehouse_uid=data.warehouse_uid
                )
                return True
            else:
                await log_error(
                    logger,
                    WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} уже привязан к другому чату"),
                    context={
                        "warehouse_uid": data.warehouse_uid,
                        "current_chat_id": warehouse.telegram_chat_id,
                        "attempted_chat_id": data.chat_id
                    }
                )
                raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} уже привязан к другому чату")

        # Проверка кода активации
        if warehouse.activation_code != data.activation_code:
            await log_warning(
                logger,
                "Неверный код активации",
                warehouse_uid=data.warehouse_uid,
                provided_code=data.activation_code,
                expected_code=warehouse.activation_code,
                chat_id=data.chat_id
            )
            raise InvalidActivationCodeException("Неверный код активации")
        
        # Активация склада
        try:
            warehouse.activate(telegram_chat_id=data.chat_id, activation_code=data.activation_code)
            
            # Сохраняем обновленный склад
            await self.warehouse_repository.update(warehouse)
            
            await log_user_action(
                logger,
                user_id=data.chat_id,
                action="warehouse_activated_successfully",
                chat_id=data.chat_id,
                warehouse_uid=warehouse.uid
            )
            
            return True
            
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_uid": data.warehouse_uid,
                    "chat_id": data.chat_id
                }
            )
            raise