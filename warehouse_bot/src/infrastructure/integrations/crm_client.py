import asyncio
import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Union

import aiohttp
from aiohttp import ClientError, ClientResponse, ClientSession
from pydantic import BaseModel, ValidationError

from warehouse_bot.config.settings import settings
from ...application.exceptions import IntegrationError
from ...domain.entities.order import Order
from ...domain.value_objects.order_status import OrderStatus

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

class CRMClient:
    """
    Клиент для интеграции с CRM системой.
    
    Предоставляет методы для взаимодействия с API CRM:
    - Отправка информации о заказах
    - Обновление статусов заказов
    - Получение статистики
    - Загрузка фотографий
    
    Атрибуты:
        base_url (str): Базовый URL API CRM
        api_token (str): Токен авторизации
        timeout (int): Таймаут запросов в секундах
        max_retries (int): Максимальное количество попыток
        retry_delay (int): Задержка между попытками в секундах
        session (Optional[ClientSession]): HTTP сессия для запросов
    """
    
    def __init__(
        self,
        base_url: str = settings.crm.base_url,
        api_token: str = settings.crm.api_token,
        timeout: int = settings.crm.timeout,
        max_retries: int = settings.crm.max_retries,
        retry_delay: int = settings.crm.retry_delay
    ):
        """
        Инициализирует CRM клиент.
        
        Args:
            base_url: Базовый URL API CRM
            api_token: Токен авторизации
            timeout: Таймаут запросов в секундах
            max_retries: Максимальное количество попыток
            retry_delay: Задержка между попытками в секундах
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session: Optional[ClientSession] = None
        
    async def __aenter__(self) -> "CRMClient":
        """
        Создает HTTP сессию при входе в контекстный менеджер.
        
        Returns:
            CRMClient: Экземпляр клиента
        """
        self.session = ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "User-Agent": f"WarehouseBot/{getattr(settings, 'app_version', '1.0.0')}"
            },
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Закрывает HTTP сессию при выходе из контекстного менеджера.
        """
        if self.session:
            await self.session.close()
            self.session = None
            
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        expected_status: int = 200
    ) -> Dict[str, Any]:
        """
        Выполняет HTTP запрос к API CRM с обработкой ошибок и повторными попытками.
        
        Args:
            method: HTTP метод (GET, POST, PUT, PATCH, DELETE)
            endpoint: Конечная точка API
            data: Тело запроса в формате JSON
            params: Параметры запроса
            expected_status: Ожидаемый HTTP статус ответа
            
        Returns:
            Dict[str, Any]: Данные ответа в формате JSON
            
        Raises:
            IntegrationError: При ошибках интеграции
        """
        if not self.session:
            raise IntegrationError("HTTP сессия не инициализирована")
            
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Логирование запроса (с маскированием чувствительных данных)
        log_data = data.copy() if data else {}
        if "token" in log_data:
            log_data["token"] = "*****"
            
        logger.debug(
            "Отправка запроса к CRM API",
            extra={
                "method": method,
                "url": url,
                "params": params,
                "data": log_data,
                "timeout": self.timeout
            }
        )
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params
                ) as response:
                    # Логирование ответа
                    response_text = await response.text()
                    
                    try:
                        response_json = json.loads(response_text)
                    except json.JSONDecodeError:
                        response_json = {"raw_response": response_text}
                        
                    logger.debug(
                        "Получен ответ от CRM API",
                        extra={
                            "status": response.status,
                            "url": url,
                            "response": response_json
                        }
                    )
                    
                    # Проверка статуса ответа
                    if response.status != expected_status:
                        # Проверка на статусы, при которых не следует повторять запрос
                        if response.status in settings.crm.no_retry_statuses and retry_count > 0:
                            raise IntegrationError(
                                f"CRM API вернул ошибку {response.status}: {response_text}",
                                status_code=response.status
                            )
                            
                        raise ClientError(
                            f"CRM API вернул неожиданный статус {response.status} вместо {expected_status}"
                        )
                        
                    return response_json
                    
            except (ClientError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError) as e:
                last_error = e
                retry_count += 1
                
                if retry_count > self.max_retries:
                    logger.error(
                        "Превышено максимальное количество попыток запроса к CRM API",
                        extra={
                            "error": str(e),
                            "retry_count": retry_count,
                            "max_retries": self.max_retries
                        }
                    )
                    raise IntegrationError(
                        f"Не удалось выполнить запрос к CRM API после {self.max_retries} попыток: {str(e)}"
                    ) from e
                    
                logger.warning(
                    "Ошибка при запросе к CRM API, повторная попытка",
                    extra={
                        "error": str(e),
                        "retry_count": retry_count,
                        "max_retries": self.max_retries,
                        "delay": self.retry_delay
                    }
                )
                await asyncio.sleep(self.retry_delay)
                
        # Этот код не должен быть достигнут, но добавлен для безопасности
        raise IntegrationError(f"Необработанная ошибка при запросе к CRM API: {last_error}")
        
    async def send_new_order(self, order: Order) -> Dict[str, Any]:
        """
        Отправляет информацию о новом заказе в CRM.
        
        Args:
            order: Объект заказа
            
        Returns:
            Dict[str, Any]: Ответ CRM системы
            
        Raises:
            IntegrationError: При ошибках интеграции
        """
        data = {
            "order_id": str(order.id),
            "warehouse_id": order.warehouse_id,
            "order_number": order.order_number,
            "created_at": order.created_at.isoformat(),
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "delivery_address": order.delivery_address,
            "items": [
                {
                    "name": item.name,
                    "quantity": item.quantity,
                    "price": float(item.price.amount)
                }
                for item in order.items
            ],
            "total_amount": float(order.total_amount.amount),
            "comment": order.comment,
            "payment_type": order.payment_type
        }
        
        return await self._make_request(
            method="POST",
            endpoint="/orders",
            data=data,
            expected_status=201
        )
        
    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        cooking_time_minutes: Optional[int] = None,
        expected_ready_at: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Обновляет статус заказа в CRM.
        
        Args:
            order_id: ID заказа
            status: Новый статус заказа
            cooking_time_minutes: Время приготовления в минутах (опционально)
            expected_ready_at: Ожидаемое время готовности (опционально)
            
        Returns:
            Dict[str, Any]: Ответ CRM системы
            
        Raises:
            IntegrationError: При ошибках интеграции
        """
        data: Dict[str, Any] = {
            "status": status.value
        }
        
        if cooking_time_minutes is not None:
            data["cooking_time_minutes"] = cooking_time_minutes
            
        if expected_ready_at is not None:
            data["expected_ready_at"] = expected_ready_at
            
        return await self._make_request(
            method="PATCH",
            endpoint=f"/orders/{order_id}/status",
            data=data
        )
        
    async def upload_order_photos(
        self,
        order_id: str,
        photo_urls: list[str]
    ) -> Dict[str, Any]:
        """
        Загружает фотографии заказа в CRM.
        
        Args:
            order_id: ID заказа
            photo_urls: Список URL фотографий
            
        Returns:
            Dict[str, Any]: Ответ CRM системы
            
        Raises:
            IntegrationError: При ошибках интеграции
        """
        data = {
            "photos": [
                {"url": url} for url in photo_urls
            ]
        }
        
        return await self._make_request(
            method="POST",
            endpoint=f"/orders/{order_id}/photos",
            data=data
        )
        
    async def get_sales_statistics(
        self,
        warehouse_id: str,
        date_from: str,
        date_to: str
    ) -> Dict[str, Any]:
        """
        Получает статистику продаж из CRM для указанного периода.
        
        Args:
            warehouse_id: ID склада
            date_from: Начальная дата в формате ISO 8601
            date_to: Конечная дата в формате ISO 8601
            
        Returns:
            Dict[str, Any]: Статистика продаж
            
        Raises:
            IntegrationError: При ошибках интеграции
        """
        params = {
            "warehouse_id": warehouse_id,
            "date_from": date_from,
            "date_to": date_to
        }
        
        return await self._make_request(
            method="GET",
            endpoint="/statistics/sales",
            params=params
        )