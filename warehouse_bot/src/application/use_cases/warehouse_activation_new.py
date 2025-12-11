from ...application.dto.incoming_orders import ActivateWarehouseDTO
from ...application.exceptions import (
    InvalidActivationCodeException,
    WarehouseNotFoundException
)
from ...domain.repositories.warehouse_repository import WarehouseRepository
from ...infrastructure.logging import get_logger, log_user_action, log_server_action, log_error, log_warning
from ...infrastructure.integrations.crm_client import CRMClient

logger = get_logger(__name__)

class ActivateWarehouseUseCase:
    """
    Use case для активации склада.
    
    Отвечает за:
    - Проверку данных склада через CRM
    - Привязку склада к Telegram-чату в локальной базе
    - Управление попытками активации
    """
    
    def __init__(
        self,
        warehouse_repository: WarehouseRepository,
        crm_client: CRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            warehouse_repository: Локальный репозиторий для сохранения данных
            crm_client: Клиент для проверки данных через CRM
        """
        self.warehouse_repository = warehouse_repository
        self.crm_client = crm_client
        
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
            warehouse_id=data.warehouse_id
        )
        
        # Проверяем данные склада через CRM
        async with self.crm_client as client:
            try:
                # Проверяем склад по ID в CRM
                response = await client._make_request(
                    method="GET",
                    endpoint=f"/warehouses/{data.warehouse_id}",
                    expected_status=200
                )
                
                if "data" not in response or not response["data"]:
                    await log_error(
                        logger,
                        WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден в CRM"),
                        context={
                            "warehouse_id": data.warehouse_id,
                            "chat_id": data.chat_id
                        }
                    )
                    raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден в CRM")
                
                crm_warehouse_data = response["data"]
                
                # Если в DTO есть код активации, проверяем его в CRM
                if data.activation_code:
                    # Для проверки кода активации используем отдельный endpoint
                    code_response = await client._make_request(
                        method="GET",
                        endpoint=f"/warehouses/by-code/{data.activation_code}",
                        expected_status=200
                    )
                    
                    if "data" not in code_response or not code_response["data"]:
                        await log_warning(
                            logger,
                            "Неверный код активации",
                            warehouse_id=data.warehouse_id,
                            provided_code=data.activation_code,
                            chat_id=data.chat_id
                        )
                        raise InvalidActivationCodeException("Неверный код активации")
                    
                    # Проверяем, что код действительно относится к этому складу
                    code_warehouses = code_response["data"]
                    if isinstance(code_warehouses, list) and len(code_warehouses) > 0:
                        code_warehouse = code_warehouses[0]
                        if str(code_warehouse.get("id", "")) != data.warehouse_id:
                            await log_warning(
                                logger,
                                "Код активации не соответствует складу",
                                warehouse_id=data.warehouse_id,
                                provided_code=data.activation_code,
                                chat_id=data.chat_id
                            )
                            raise InvalidActivationCodeException("Код активации не соответствует складу")
                
                # Получаем информацию о складе из локальной базы
                local_warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
                
                # Если склада нет в локальной базе, создаем его на основе данных из CRM
                if not local_warehouse:
                    from ...domain.entities.warehouse import Warehouse
                    local_warehouse = Warehouse(
                        id=str(crm_warehouse_data.get("id", data.warehouse_id)),
                        name=crm_warehouse_data.get("name", ""),
                        address=crm_warehouse_data.get("address", ""),
                        telegram_chat_id=None,  # Будет установлен при активации
                        activation_code=crm_warehouse_data.get("activation_code") or data.activation_code
                    )
                
                # Проверка, не активирован ли склад уже в локальной базе
                if local_warehouse.is_active and local_warehouse.telegram_chat_id is not None:
                    await log_warning(
                        logger,
                        "Склад уже активирован",
                        warehouse_id=data.warehouse_id,
                        current_chat_id=local_warehouse.telegram_chat_id,
                        attempted_chat_id=data.chat_id
                    )
                    # Если склад уже привязан к этому же чату - возвращаем успех
                    if local_warehouse.telegram_chat_id == data.chat_id:
                        await log_server_action(
                            logger,
                            action="warehouse_already_activated_same_chat",
                            result="success",
                            warehouse_id=data.warehouse_id
                        )
                        return True
                    else:
                        await log_error(
                            logger,
                            WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} уже привязан к другому чату"),
                            context={
                                "warehouse_id": data.warehouse_id,
                                "current_chat_id": local_warehouse.telegram_chat_id,
                                "attempted_chat_id": data.chat_id
                            }
                        )
                        raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} уже привязан к другому чату")
                
                # Активация склада в локальной базе
                try:
                    local_warehouse.activate(telegram_chat_id=data.chat_id, activation_code=data.activation_code)
                    
                    # Сохраняем обновленный склад в локальной базе
                    await self.warehouse_repository.update(local_warehouse)
                    
                    await log_user_action(
                        logger,
                        user_id=data.chat_id,
                        action="warehouse_activated_successfully",
                        chat_id=data.chat_id,
                        warehouse_id=local_warehouse.id
                    )
                    
                    return True
                    
                except Exception as e:
                    await log_error(
                        logger,
                        e,
                        context={
                            "warehouse_id": data.warehouse_id,
                            "chat_id": data.chat_id
                        }
                    )
                    raise
                    
            except Exception as e:
                await log_error(
                    logger,
                    e,
                    context={
                        "warehouse_id": data.warehouse_id,
                        "chat_id": data.chat_id,
                        "action": "crm_validation"
                    }
                )
                raise