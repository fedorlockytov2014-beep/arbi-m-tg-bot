from typing import List, Optional
import logging

from ....domain.entities.warehouse import Warehouse
from ....domain.repositories.warehouse_repository import WarehouseRepository
from ....infrastructure.logging import get_logger, log_server_action, log_error
from ....infrastructure.integrations.crm_client import CRMClient
from ....domain.entities.warehouse import Warehouse
from ....domain.value_objects.warehouse_id import WarehouseId

logger = get_logger(__name__)


class WarehouseRepositoryImpl(WarehouseRepository):
    """
    Реализация репозитория складов с использованием CRM API.
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
        Получает склад по ID.
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
                        id=WarehouseId(warehouse_data.get("id", warehouse_id)),
                        uid=warehouse_data.get("uid", ""),
                        name=warehouse_data.get("name", ""),
                        address=warehouse_data.get("address", ""),
                        telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                        activation_code=warehouse_data.get("activation_code")
                    )
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "action": "get_by_id"
                }
            )
        
        return None
    
    async def get_by_uid(self, warehouse_uid: str) -> Optional[Warehouse]:
        """
        Получает склад по UID.
        """
        log_server_action(
            logger,
            action="warehouse_get_by_uid",
            warehouse_uid=warehouse_uid
        )
        
        try:
            async with self._crm_client as client:
                response = await client.get_warehouse_by_uid(warehouse_uid)
                
                if "data" in response and response["data"]:
                    warehouses_data = response["data"]
                    # Возвращаем первый склад из результата
                    if isinstance(warehouses_data, list) and len(warehouses_data) > 0:
                        warehouse_data = warehouses_data[0]
                        warehouse = Warehouse(
                            id=WarehouseId(warehouse_data.get("id", warehouse_uid)),
                            uid=warehouse_data.get("uid", warehouse_uid),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                            activation_code=warehouse_data.get("activation_code")
                        )
                        
                        log_server_action(
                            logger,
                            action="warehouse_found_by_uid",
                            result="success",
                            warehouse_uid=warehouse_uid
                        )
                        
                        return warehouse
                    elif isinstance(warehouses_data, dict):
                        # Если возвращается один объект, а не массив
                        warehouse = Warehouse(
                            id=WarehouseId(warehouses_data.get("id", warehouse_uid)),
                            uid=warehouses_data.get("uid", warehouse_uid),
                            name=warehouses_data.get("name", ""),
                            address=warehouses_data.get("address", ""),
                            telegram_chat_id=warehouses_data.get("telegram_chat_id"),
                            activation_code=warehouses_data.get("activation_code")
                        )
                        
                        log_server_action(
                            logger,
                            action="warehouse_found_by_uid",
                            result="success",
                            warehouse_uid=warehouse_uid
                        )
                        
                        return warehouse
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "warehouse_uid": warehouse_uid,
                    "action": "get_by_uid"
                }
            )
            
            log_server_action(
                logger,
                action="warehouse_not_found_by_uid",
                result="error",
                warehouse_uid=warehouse_uid
            )
        
        return None
    
    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает склад по ID Telegram-чата.
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
                            id=WarehouseId(warehouse_data.get("id", "")),
                            uid=warehouse_data.get("uid", ""),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id", chat_id),
                            activation_code=warehouse_data.get("activation_code")
                        )
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "chat_id": chat_id,
                    "action": "get_by_telegram_chat_id"
                }
            )
        
        return None
    
    async def get_all(self) -> List[Warehouse]:
        """
        Получает все склады.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/warehouses",
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    warehouses_data = response["data"]
                    warehouses = []
                    
                    for warehouse_data in warehouses_data:
                        warehouse = Warehouse(
                            id=WarehouseId(warehouse_data.get("id", "")),
                            uid=warehouse_data.get("uid", ""),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                            activation_code=warehouse_data.get("activation_code")
                        )
                        warehouses.append(warehouse)
                    
                    return warehouses
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "action": "get_all"
                }
            )
        
        return []
    
    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохраняет склад.
        """
        log_server_action(
            logger,
            action="warehouse_save",
            warehouse_uid=warehouse.uid
        )
        
        try:
            async with self._crm_client as client:
                data = {
                    "data": {
                        "uid": warehouse.uid,
                        "name": warehouse.name,
                        "address": warehouse.address,
                        "telegram_chat_id": warehouse.telegram_chat_id,
                        "activation_code": warehouse.activation_code
                    }
                }
                
                response = await client._make_request(
                    method="POST",
                    endpoint="/warehouses",
                    data=data,
                    expected_status=201
                )
                
                if "data" in response and response["data"]:
                    saved_data = response["data"]
                    result = Warehouse(
                        id=WarehouseId(saved_data.get("id", warehouse.id)),
                        uid=saved_data.get("uid", warehouse.uid),
                        name=saved_data.get("name", warehouse.name),
                        address=saved_data.get("address", warehouse.address),
                        telegram_chat_id=saved_data.get("telegram_chat_id", warehouse.telegram_chat_id),
                        activation_code=saved_data.get("activation_code", warehouse.activation_code)
                    )
                    
                    log_server_action(
                        logger,
                        action="warehouse_saved_successfully",
                        result="success",
                        warehouse_uid=warehouse.uid
                    )
                    
                    return result
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "warehouse_uid": warehouse.uid,
                    "action": "save"
                }
            )
            raise
        
        return warehouse
    
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет склад.
        """
        log_server_action(
            logger,
            action="warehouse_update",
            warehouse_uid=warehouse.uid,
            warehouse_id=warehouse.id
        )
        
        try:
            async with self._crm_client as client:
                data = {
                    "data": {
                        "uid": warehouse.uid,
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
                        id=WarehouseId(updated_data.get("id", warehouse.id)),
                        uid=updated_data.get("uid", warehouse.uid),
                        name=updated_data.get("name", warehouse.name),
                        address=updated_data.get("address", warehouse.address),
                        telegram_chat_id=updated_data.get("telegram_chat_id", warehouse.telegram_chat_id),
                        activation_code=updated_data.get("activation_code", warehouse.activation_code)
                    )
                    
                    log_server_action(
                        logger,
                        action="warehouse_updated_successfully",
                        result="success",
                        warehouse_uid=warehouse.uid
                    )
                    
                    return result
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "warehouse_uid": warehouse.uid,
                    "warehouse_id": warehouse.id,
                    "action": "update"
                }
            )
            raise
        
        return warehouse
    
    async def delete(self, warehouse_id: str) -> bool:
        """
        Удаляет склад.
        """
        log_server_action(
            logger,
            action="warehouse_delete",
            warehouse_id=warehouse_id
        )
        
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="DELETE",
                    endpoint=f"/warehouses/{warehouse_id}",
                    expected_status=200
                )
                
                log_server_action(
                    logger,
                    action="warehouse_deleted_successfully",
                    result="success",
                    warehouse_id=warehouse_id
                )
                
                return True
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "action": "delete"
                }
            )
            return False
    
    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/warehouses",
                    params={"filters[activation_code][$eq]": activation_code},
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    warehouses_data = response["data"]
                    if isinstance(warehouses_data, list) and len(warehouses_data) > 0:
                        warehouse_data = warehouses_data[0]
                        return Warehouse(
                            id=WarehouseId(warehouse_data.get("id", "")),
                            uid=warehouse_data.get("uid", ""),
                            name=warehouse_data.get("name", ""),
                            address=warehouse_data.get("address", ""),
                            telegram_chat_id=warehouse_data.get("telegram_chat_id"),
                            activation_code=warehouse_data.get("activation_code", activation_code)
                        )
        except Exception as e:
            log_error(
                logger,
                e,
                context={
                    "activation_code": activation_code,
                    "action": "find_by_activation_code"
                }
            )
        
        return None