from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import hmac
import json
from typing import Dict, Any

from warehouse_bot.config.settings import settings
from ...application.dto.incoming_orders import CreateOrderDTO
from ...domain.repositories.warehouse_repository import IWarehouseRepository
from ...infrastructure.integrations.crm_client import CRMClient
from aiogram import Bot


class WebhookHandler:
    """
    Обработчик вебхуков от CRM системы.
    """

    def __init__(
        self,
        warehouse_repository: IWarehouseRepository,
        crm_client: CRMClient,
        bot: Bot,
        secret_key: str = settings.webhook.secret_key
    ):
        self.warehouse_repository = warehouse_repository
        self.crm_client = crm_client
        self.bot = bot
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
            warehouse = await self.warehouse_repository.get_by_id(order_data.warehouse_id)
            if not warehouse:
                raise HTTPException(status_code=404, detail=f"Warehouse {order_data.warehouse_id} not found")

            # Проверяем, что склад активирован
            if not warehouse.is_active or not warehouse.telegram_chat_id:
                raise HTTPException(status_code=400, detail="Warehouse is not active or not linked to chat")

            # Формируем сообщение о новом заказе в соответствии с ТЗ
            items_text = "\n".join([
                f" • {item['name']} ×{item['quantity']} — {item['price']} ₽"
                for item in order_data.items
            ])
            
            order_message = (
                f"🆕 Новый заказ №ZK-{order_data.order_id}\n"
                f"Клиент: {order_data.customer_name}\n"
                f"Телефон: {order_data.customer_phone}\n"
                f"Адрес: {order_data.delivery_address}\n"
                f"Комментарий: {order_data.comment or 'нет'}\n\n"
                f"Состав:\n{items_text}\n"
                f"Итог: {order_data.total_amount} ₽"
            )

            # Отправляем сообщение в Telegram
            try:
                from warehouse_bot.src.presentation.keyboards.inline_keyboards import get_order_actions_keyboard
                await self.bot.send_message(
                    chat_id=warehouse.telegram_chat_id,
                    text=order_message,
                    reply_markup=get_order_actions_keyboard(str(order_data.order_id))
                )
            except Exception as e:
                # Логируем ошибку, но возвращаем успех, чтобы CRM не повторяла отправку
                print(f"Error sending order notification to Telegram: {str(e)}")

            return {"status": "success", "order_id": order_data.order_id}

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
            # Пока просто возвращаем успешный ответ
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
        # Преобразуем payload в строку для подписи
        payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)