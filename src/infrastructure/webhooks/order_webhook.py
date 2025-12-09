import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from config.settings import settings
from src.application.dto.incoming_orders import NewOrderDTO
from src.application.use_cases.order_management import AcceptOrderUseCase
from src.domain.repositories.warehouse_repository import WarehouseRepository
from src.presentation.bot.dispatcher import bot
from src.presentation.formatters.order_formatter import format_new_order_message
from src.presentation.keyboards.inline_keyboards import get_accept_order_keyboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


class OrderWebhookHandler:
    """
    Обработчик webhook-запросов от CRM системы.
    
    Обрабатывает:
    - Новые заказы от CRM
    - Обновления статусов заказов
    - Проверяет подпись запроса для безопасности
    """
    
    def __init__(
        self,
        warehouse_repository: WarehouseRepository,
    ):
        self.warehouse_repository = warehouse_repository
        
    async def verify_signature(self, body: bytes, signature: str) -> bool:
        """
        Проверяет подпись запроса для безопасности.
        
        Args:
            body: Тело запроса
            signature: Подпись из заголовка X-Signature
            
        Returns:
            bool: True если подпись верна
        """
        if not settings.webhook.secret_key:
            # Если секретный ключ не задан, пропускаем проверку
            return True
            
        expected_signature = hmac.new(
            key=settings.webhook.secret_key.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_new_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает новый заказ от CRM.
        
        Args:
            order_data: Данные заказа из CRM
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        logger.info(
            "Получен новый заказ от CRM",
            order_id=order_data.get("id"),
            warehouse_id=order_data.get("warehouse_id")
        )
        
        try:
            # Получаем информацию о складе
            warehouse = await self.warehouse_repository.get_by_uid(order_data["warehouse_id"])
            if not warehouse:
                logger.warning(
                    "Заказ проигнорирован — склад не найден",
                    order_id=order_data.get("id"),
                    warehouse_id=order_data.get("warehouse_id")
                )
                return {"status": "error", "message": "Warehouse not found"}
            
            # Отправляем сообщение в чат
            chat_id = warehouse.telegram_chat_id
            if not chat_id:
                logger.warning(
                    "Заказ проигнорирован — чат не привязан",
                    order_id=order_data.get("id"),
                    warehouse_id=order_data.get("warehouse_id")
                )
                return {"status": "error", "message": "Chat not linked to warehouse"}
            
            # Форматируем сообщение о заказе
            order_message = format_new_order_message(order_data)
            
            # Отправляем сообщение с кнопками
            keyboard = get_accept_order_keyboard(order_data["id"])
            
            await bot.send_message(
                chat_id=chat_id,
                text=order_message,
                reply_markup=keyboard
            )
            
            logger.info(
                "Заказ успешно отправлен в чат",
                order_id=order_data.get("id"),
                chat_id=chat_id
            )
            
            return {"status": "success", "message": "Order sent to chat"}
            
        except Exception as e:
            logger.error(
                "Ошибка при обработке нового заказа",
                order_id=order_data.get("id"),
                error=str(e),
                exc_info=True
            )
            raise
    
    async def handle_order_status_update(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает обновление статуса заказа от CRM.
        
        Args:
            status_data: Данные обновления статуса
            
        Returns:
            Dict[str, Any]: Результат обработки
        """
        logger.info(
            "Получено обновление статуса заказа",
            order_id=status_data.get("order_id"),
            new_status=status_data.get("status")
        )
        
        # TODO: Реализовать обработку обновления статуса
        # Например, уведомление в чат если заказ отменён
        
        return {"status": "success", "message": "Status update processed"}
    
    async def create_webhook_router(self) -> APIRouter:
        """
        Создает и возвращает FastAPI роутер для webhook-эндпоинтов.
        
        Returns:
            APIRouter: Роутер с webhook-эндпоинтами
        """
        router = APIRouter(prefix="/webhook", tags=["webhooks"])
        
        @router.post("/order")
        async def new_order_webhook(
            request: Request,
            background_tasks: BackgroundTasks
        ) -> Dict[str, Any]:
            """
            Webhook для получения новых заказов от CRM.
            
            Args:
                request: HTTP запрос
                background_tasks: Фоновые задачи
                
            Returns:
                Dict[str, Any]: Результат обработки
            """
            # Получаем тело запроса
            body = await request.body()
            
            # Проверяем подпись если она есть
            signature = request.headers.get("X-Signature")
            if signature and not await self.verify_signature(body, signature):
                logger.warning("Неверная подпись webhook запроса")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            try:
                order_data = json.loads(body.decode())
            except json.JSONDecodeError as e:
                logger.error("Неверный формат JSON в webhook", error=str(e))
                raise HTTPException(status_code=400, detail="Invalid JSON")
            
            # Обрабатываем заказ в фоне
            background_tasks.add_task(self.handle_new_order, order_data)
            
            return {"status": "accepted", "message": "Order received and processing"}
        
        @router.post("/order/status")
        async def order_status_webhook(
            request: Request,
            background_tasks: BackgroundTasks
        ) -> Dict[str, Any]:
            """
            Webhook для получения обновлений статуса заказа от CRM.
            
            Args:
                request: HTTP запрос
                background_tasks: Фоновые задачи
                
            Returns:
                Dict[str, Any]: Результат обработки
            """
            # Получаем тело запроса
            body = await request.body()
            
            # Проверяем подпись если она есть
            signature = request.headers.get("X-Signature")
            if signature and not await self.verify_signature(body, signature):
                logger.warning("Неверная подпись webhook запроса")
                raise HTTPException(status_code=401, detail="Invalid signature")
            
            try:
                status_data = json.loads(body.decode())
            except json.JSONDecodeError as e:
                logger.error("Неверный формат JSON в webhook", error=str(e))
                raise HTTPException(status_code=400, detail="Invalid JSON")
            
            # Обрабатываем обновление статуса в фоне
            background_tasks.add_task(self.handle_order_status_update, status_data)
            
            return {"status": "accepted", "message": "Status update received and processing"}
        
        return router


# Глобальный экземпляр для использования в приложении
order_webhook_handler: Optional[OrderWebhookHandler] = None


def get_order_webhook_handler() -> OrderWebhookHandler:
    """Возвращает глобальный экземпляр обработчика webhook."""
    global order_webhook_handler
    if order_webhook_handler is None:
        raise RuntimeError("OrderWebhookHandler не инициализирован")
    return order_webhook_handler