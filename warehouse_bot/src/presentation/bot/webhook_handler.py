from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import hmac
from typing import Dict, Any

from ...application.dto.incoming_orders import CreateOrderDTO
from ...application.use_cases.order_management import AcceptOrderUseCase
from ...domain.repositories.warehouse_repository import WarehouseRepository
from ...infrastructure.integrations.crm_client import CRMClient
from ...config.settings import settings


class WebhookHandler:
    """
    Обработчик вебхуков от CRM системы.
    """
    
    def __init__(
        self,
        warehouse_repository: WarehouseRepository,
        crm_client: CRMClient,
        secret_key: str = settings.webhook.secret_key
    ):
        self.warehouse_repository = warehouse_repository
        self.crm_client = crm_client
        self.secret_key = secret_key
        self.security = HTTPBearer()
        
    def create_app(self) -> FastAPI:
        """
        Создает и возвращает FastAPI приложение для обработки вебхуков.
        """
        app = FastAPI(title="Warehouse Bot Webhook API")
        
        @app.post("/webhook/order")
        async def handle_new_order_webhook(
            payload: Dict[str, Any],
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Обработка вебхука нового заказа от CRM.
            
            Args:
                payload: JSON-данные заказа
                credentials: Авторизационные данные
            """
            # Проверяем подпись
            if not self._verify_signature(payload, credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Валидация данных заказа
            try:
                order_data = CreateOrderDTO(**payload)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid order data: {str(e)}")
            
            # Получаем склад по ID
            warehouse = await self.warehouse_repository.get_by_uid(order_data.warehouse_id)
            if not warehouse:
                raise HTTPException(status_code=404, detail=f"Warehouse {order_data.warehouse_id} not found")
            
            # Проверяем, что склад активирован
            if not warehouse.is_active or not warehouse.telegram_chat_id:
                raise HTTPException(status_code=400, detail="Warehouse is not active or not linked to chat")
            
            # В реальной реализации здесь нужно отправить сообщение в Telegram
            # через бот API с информацией о новом заказе
            # Пока просто возвращаем успешный ответ
            return {"status": "success", "order_id": order_data.order_number}
        
        @app.post("/webhook/order/status")
        async def handle_order_status_webhook(
            payload: Dict[str, Any],
            credentials: HTTPAuthorizationCredentials = Depends(self.security)
        ):
            """
            Обработка вебхука изменения статуса заказа от CRM.
            
            Args:
                payload: JSON-данные обновления статуса
                credentials: Авторизационные данные
            """
            # Проверяем подпись
            if not self._verify_signature(payload, credentials.credentials):
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            # Обновляем статус заказа в системе
            order_id = payload.get("order_id")
            new_status = payload.get("status")
            
            if not order_id or not new_status:
                raise HTTPException(status_code=400, detail="Missing order_id or status")
            
            # В реальной реализации здесь нужно обновить статус заказа
            # и, возможно, отправить уведомление в Telegram
            return {"status": "success", "order_id": order_id}
        
        return app
    
    def _verify_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Проверяет подпись вебхука.
        
        Args:
            payload: Данные вебхука
            signature: Подпись для проверки
            
        Returns:
            bool: True если подпись действительна
        """
        expected_signature = hmac.new(
            self.secret_key.encode(),
            str(payload).encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)