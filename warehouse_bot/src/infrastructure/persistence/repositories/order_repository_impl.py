from typing import List, Optional

from ....domain.repositories.order_repository import OrderRepository
from ....domain.value_objects.order_status import OrderStatus
from ....infrastructure.integrations.crm_client import CRMClient
from ....domain.entities.order import Order
from ....domain.entities.order_item import OrderItem
from ....domain.value_objects.money import Money
from ....infrastructure.logging import get_logger, log_server_action, log_error

logger = get_logger(__name__)


class OrderRepositoryImpl(OrderRepository):
    """
    Реализация репозитория заказов с использованием CRM API.
    """
    
    def __init__(self, crm_client: CRMClient):
        """
        Инициализирует репозиторий с CRM клиентом.
        
        Args:
            crm_client: Клиент для взаимодействия с CRM API
        """
        self._crm_client = crm_client
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Получает заказ по ID.
        """
        try:
            async with self._crm_client as client:
                response = await client.get_order_details(order_id)
                
                if "data" in response and response["data"]:
                    order_data = response["data"]
                    return self._map_order_from_crm(order_data)
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "order_id": order_id,
                    "action": "get_by_id"
                }
            )
        
        return None
    
    async def get_by_number(self, order_number: str) -> Optional[Order]:
        """
        Получает заказ по номеру.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/orders",
                    params={"filters[order_number][$eq]": order_number},
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    orders_data = response["data"]
                    if isinstance(orders_data, list) and len(orders_data) > 0:
                        order_data = orders_data[0]
                        return self._map_order_from_crm(order_data)
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "order_number": order_number,
                    "action": "get_by_number"
                }
            )
        
        return None
    
    async def get_by_warehouse_and_status(
        self, 
        warehouse_id: str, 
        status: OrderStatus
    ) -> List[Order]:
        """
        Получает заказы по складу и статусу.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/orders",
                    params={
                        "filters[warehouse][id][$eq]": warehouse_id,
                        "filters[status][$eq]": status.value
                    },
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    orders_data = response["data"]
                    if isinstance(orders_data, list):
                        orders = []
                        for order_data in orders_data:
                            orders.append(self._map_order_from_crm(order_data))
                        return orders
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "status": status.value if status else None,
                    "action": "get_by_warehouse_and_status"
                }
            )
        
        return []
    
    async def get_all_by_warehouse(self, warehouse_id: str) -> List[Order]:
        """
        Получает все заказы по складу.
        """
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="GET",
                    endpoint="/orders",
                    params={"filters[warehouse][id][$eq]": warehouse_id},
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    orders_data = response["data"]
                    if isinstance(orders_data, list):
                        orders = []
                        for order_data in orders_data:
                            orders.append(self._map_order_from_crm(order_data))
                        return orders
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "action": "get_all_by_warehouse"
                }
            )
        
        return []
    
    async def save(self, order: Order) -> Order:
        """
        Сохраняет заказ.
        """
        await log_server_action(
            logger,
            action="order_save",
            order_id=str(order.id)
        )
        
        try:
            async with self._crm_client as client:
                data = {
                    "data": {
                        "order_number": order.order_number,
                        "warehouse_id": str(order.warehouse_id),
                        "customer_name": order.customer_name,
                        "customer_phone": order.customer_phone,
                        "delivery_address": order.delivery_address,
                        "status": order.status.value,
                        "comment": order.comment,
                        "payment_type": order.payment_type,
                        "items": [
                            {
                                "name": item.name,
                                "quantity": item.quantity,
                                "price": float(item.price.amount)
                            }
                            for item in order.items
                        ],
                        "total_amount": float(order.total_amount.amount)
                    }
                }
                
                response = await client._make_request(
                    method="POST",
                    endpoint="/orders",
                    data=data,
                    expected_status=201
                )
                
                if "data" in response and response["data"]:
                    saved_data = response["data"]
                    result = self._map_order_from_crm(saved_data)
                    
                    await log_server_action(
                        logger,
                        action="order_saved_successfully",
                        result="success",
                        order_id=str(result.id)
                    )
                    
                    return result
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "action": "save"
                }
            )
            raise
        
        return order
    
    async def update(self, order: Order) -> Order:
        """
        Обновляет заказ.
        """
        await log_server_action(
            logger,
            action="order_update",
            order_id=str(order.id)
        )
        
        try:
            async with self._crm_client as client:
                data = {
                    "data": {
                        "order_number": order.order_number,
                        "warehouse_id": str(order.warehouse_id),
                        "customer_name": order.customer_name,
                        "customer_phone": order.customer_phone,
                        "delivery_address": order.delivery_address,
                        "status": order.status.value,
                        "comment": order.comment,
                        "payment_type": order.payment_type,
                        "items": [
                            {
                                "name": item.name,
                                "quantity": item.quantity,
                                "price": float(item.price.amount)
                            }
                            for item in order.items
                        ],
                        "total_amount": float(order.total_amount.amount)
                    }
                }
                
                response = await client._make_request(
                    method="PUT",
                    endpoint=f"/orders/{order.id}",
                    data=data,
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    updated_data = response["data"]
                    result = self._map_order_from_crm(updated_data)
                    
                    await log_server_action(
                        logger,
                        action="order_updated_successfully",
                        result="success",
                        order_id=str(result.id)
                    )
                    
                    return result
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "order_id": str(order.id),
                    "order_number": order.order_number,
                    "action": "update"
                }
            )
            raise
        
        return order
    
    async def delete(self, order_id: str) -> bool:
        """
        Удаляет заказ.
        """
        await log_server_action(
            logger,
            action="order_delete",
            order_id=order_id
        )
        
        try:
            async with self._crm_client as client:
                response = await client._make_request(
                    method="DELETE",
                    endpoint=f"/orders/{order_id}",
                    expected_status=200
                )
                
                await log_server_action(
                    logger,
                    action="order_deleted_successfully",
                    result="success",
                    order_id=order_id
                )
                
                return True
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "order_id": order_id,
                    "action": "delete"
                }
            )
            return False
    
    async def get_orders_by_status_for_period(
        self,
        warehouse_id: str,
        statuses: List[OrderStatus],
        date_from: str,
        date_to: str
    ) -> List[Order]:
        """
        Получает заказы по статусам за определённый период.
        """
        try:
            async with self._crm_client as client:
                # Формируем параметры фильтрации
                params = {
                    "filters[warehouse][id][$eq]": warehouse_id,
                    "filters[createdAt][$gte]": date_from,
                    "filters[createdAt][$lte]": date_to,
                }
                
                # Добавляем фильтр по статусам
                for i, status in enumerate([s.value for s in statuses]):
                    params[f"filters[status][$in][{i}]"] = status
                
                response = await client._make_request(
                    method="GET",
                    endpoint="/orders",
                    params=params,
                    expected_status=200
                )
                
                if "data" in response and response["data"]:
                    orders_data = response["data"]
                    if isinstance(orders_data, list):
                        orders = []
                        for order_data in orders_data:
                            orders.append(self._map_order_from_crm(order_data))
                        return orders
        except Exception as e:
            await log_error(
                logger,
                e,
                context={
                    "warehouse_id": warehouse_id,
                    "statuses": [s.value for s in statuses],
                    "date_from": date_from,
                    "date_to": date_to,
                    "action": "get_orders_by_status_for_period"
                }
            )
        
        return []
    
    def _map_order_from_crm(self, order_data: dict) -> Order:
        """
        Преобразует данные заказа из CRM в доменную сущность.
        
        Args:
            order_data: Словарь с данными заказа из CRM
            
        Returns:
            Order: Доменная сущность заказа
        """
        # Преобразуем items
        items = []
        if "items" in order_data:
            for item_data in order_data["items"]:
                item = OrderItem(
                    name=item_data.get("name", ""),
                    quantity=item_data.get("quantity", 1),
                    price=Money(item_data.get("price", 0.0))
                )
                items.append(item)
        
        # Преобразуем статус
        status_value = order_data.get("status", "new")
        status = OrderStatus.from_value(status_value)
        
        return Order(
            id=order_data.get("id", ""),
            order_number=order_data.get("order_number", ""),
            warehouse_id=order_data.get("warehouse_id", ""),
            customer_name=order_data.get("customer_name", ""),
            customer_phone=order_data.get("customer_phone", ""),
            delivery_address=order_data.get("delivery_address", ""),
            status=status,
            items=items,
            total_amount=Money(order_data.get("total_amount", 0.0)),
            comment=order_data.get("comment", ""),
            payment_type=order_data.get("payment_type", "cash"),
            created_at=order_data.get("created_at")
        )