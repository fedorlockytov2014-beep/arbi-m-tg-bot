from typing import List, Optional

from ....domain.repositories.warehouse_repository import IWarehouseRepository
from ....infrastructure.logging import get_logger, log_server_action, log_error
from ....infrastructure.integrations.crm_client import CRMClient
from ....domain.entities.warehouse import Warehouse

logger = get_logger(__name__)


class WarehouseCrmRepositoryImpl(IWarehouseRepository):
    """
    Реализация репозитория складов с использованием CRM API для проверки данных.
    """
    
    def __init__(self, crm_client: CRMClient):
        """
        Инициализирует репозиторий с CRM клиентом.
        
        Args:
            crm_client: Клиент для взаимодействия с CRM API
        """
        self._crm_client = crm_client
    
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """
        Получает склад по ID из CRM.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint=f"/warehouses/{warehouse_id}",
                    expected_status=200
                )

                if "data" in response and response["data"]:
                    warehouse_data = response["data"]
                    return Warehouse(
                        id=str(warehouse_data.get("id", warehouse_id)),
                        name=warehouse_data.get("name", ""),
                        address=warehouse_data.get("address", ""),
                        telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                        activation_code=warehouse_data.get("activationCode")
                    )
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "action": "get_by_id"
                }
            )
        
        return None

    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID Telegram-чата из CRM.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/warehouses",
                    params={"filters[telegram_chat_id][$eq]": str(chat_id)},
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    warehouses_data = response["data"]
                    if isinstance(warehouses_data, list) and len(warehouses_data) > 0:
                        warehouse_data = warehouses_data[0]
                        return Warehouse(
                            id=str(warehouse_data.get("id", "")),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id", chat_id),
                            activation_code=warehouse_data.get("activation_code")
                        )
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "chat_id": chat_id,
                    "action": "get_by_telegram_chat_id"
                }
            )
        
        return None


    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет склад в CRM.
        """
        await log_server_action(
            logger,
            action="warehouse_update",
            warehouse_id=warehouse.id
        )
        
        try:
            async with self._crm_client as client:
                data = {
                    "data": {
                        "id": warehouse.id,
                        "name": warehouse.name,
                        "address": warehouse.address,
                        "telegram_chat_id": warehouse.telegram_chat_id,
                        "activation_code": warehouse.activation_code
                    }
                }
                
                response = await client._make_request(
                    method="PUT",
                    endpoint=f"/warehouses/{warehouse.id}",
                    data=data,
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    updated_data = response["data"]
                    result = Warehouse(
                        id=str(updated_data.get("id", warehouse.id)),
                        name=updated_data.get("name", warehouse.name),
                        address=updated_data.get("address", warehouse.address),
                        telegram_chat_id=updated_data.get("telegram_chat_id", warehouse.telegram_chat_id),
                        activation_code=updated_data.get("activation_code", warehouse.activation_code)
                    )
                    
                    await log_server_action(
                        logger,
                        action="warehouse_updated_successfully",
                        result="success",
                        warehouse_id=warehouse.id
                    )
                    
                    return result
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse.id,
                    "action": "update"
                }
            )
            raise
        
        return warehouse

    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации в CRM.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint=f"/warehouses/by-code/{activation_code}",
                    expected_status=200
                )
                if "data" in response and response["data"]:
                    warehouses_data = response["data"]
                    if isinstance(warehouses_data, list) and len(warehouses_data) > 0:
                        warehouse_data = warehouses_data[0]
                        return Warehouse(
                            id=str(warehouse_data.get("id", "")),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                            activation_code=warehouse_data.get("activationCode", activation_code)
                        )
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "activation_code": activation_code,
                    "action": "find_by_activation_code"
                }
            )
        
        return None