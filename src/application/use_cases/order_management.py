import logging
from datetime import datetime, timedelta
from typing import Optional

from src.application.dto.incoming_orders import AcceptOrderDTO, SetCookingTimeDTO, ConfirmReadyDTO
from src.application.exceptions import (
    OrderAlreadyAcceptedException,
    OrderAlreadyCompletedException,
    OrderNotFoundException,
    WarehouseNotFoundException
)
from src.domain.entities.order import Order
from src.domain.repositories.order_repository import OrderRepository
from src.domain.repositories.warehouse_repository import WarehouseRepository
from src.domain.services.order_service import OrderService
from src.domain.value_objects.cooking_time import CookingTime
from src.domain.value_objects.order_status import OrderStatus

logger = logging.getLogger(__name__)


class AcceptOrderUseCase:
    """
    Use case для принятия заказа партнером.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку, что заказ еще не принят другим партнером
    - Обновление статуса заказа
    - Сохранение времени принятия заказа
    
    Атрибуты:
        order_repository: Репозиторий для работы с заказами
        warehouse_repository: Репозиторий для работы со складами
        order_service: Сервис для бизнес-логики заказов
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        warehouse_repository: WarehouseRepository,
        order_service: OrderService,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        
    async def execute(self, data: AcceptOrderDTO) -> Order:
        """
        Выполняет сценарий принятия заказа.
        
        Args:
            data: DTO с данными для принятия заказа
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
            OrderAlreadyAcceptedException: Если заказ уже принят другим партнером
        """
        logger.info(
            "Начало выполнения сценария принятия заказа",
            order_id=data.order_id,
            chat_id=data.chat_id,
            warehouse_id=data.warehouse_uid
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_uid(data.warehouse_uid)
        if not warehouse:
            logger.error(
                "Склад не найден при попытке принять заказ",
                warehouse_uid=data.warehouse_uid,
                order_id=data.order_id
            )
            raise WarehouseNotFoundException(f"Склад с UID {data.warehouse_uid} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            logger.error(
                "Попытка принять заказ для чужого склада",
                warehouse_uid=data.warehouse_uid,
                chat_id=data.chat_id,
                warehouse_chat_id=warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с UID {data.warehouse_uid} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            logger.error(
                "Заказ не найден при попытке принять",
                order_id=data.order_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ еще не принят
        if order.status != OrderStatus.SENT_TO_PARTNER:
            logger.warning(
                "Попытка принять заказ, который уже в работе",
                order_id=data.order_id,
                current_status=order.status.value
            )
            # Если заказ уже принят этим же складом - возвращаем его без ошибки
            if order.warehouse_id == data.warehouse_uid and order.status == OrderStatus.ACCEPTED_BY_PARTNER:
                logger.info(
                    "Заказ уже принят этим складом, возврат текущего состояния",
                    order_id=data.order_id
                )
                return order
                
            raise OrderAlreadyAcceptedException(
                f"Заказ уже принят со статусом: {order.status.value}"
            )
            
        # Проверка, что заказ относится к этому складу
        if order.warehouse_id != data.warehouse_uid:
            logger.error(
                "Попытка принять заказ, не относящийся к складу",
                order_id=data.order_id,
                order_warehouse_id=order.warehouse_id,
                target_warehouse_id=data.warehouse_uid
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не относится к складу {data.warehouse_uid}")
            
        # Обновление статуса заказа
        try:
            updated_order = await self.order_service.accept_order(
                order=order,
                accepted_at=datetime.utcnow()
            )
            
            logger.info(
                "Заказ успешно принят",
                order_id=updated_order.id,
                warehouse_id=updated_order.warehouse_id,
                accepted_at=updated_order.accepted_at
            )
            
            return updated_order
            
        except Exception as e:
            logger.error(
                "Ошибка при принятии заказа",
                order_id=data.order_id,
                error=str(e),
                exc_info=True
            )
            raise


class SetCookingTimeUseCase:
    """
    Use case для установки времени готовки заказа.
    
    Отвечает за:
    - Проверку, что заказ принадлежит складу
    - Установку времени готовки
    - Обновление статуса заказа на 'cooking'
    - Расчет времени готовности
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        warehouse_repository: WarehouseRepository,
        order_service: OrderService,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        
    async def execute(self, data: SetCookingTimeDTO) -> Order:
        """
        Выполняет сценарий установки времени готовки.
        
        Args:
            data: DTO с данными для установки времени готовки
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
        """
        logger.info(
            "Начало выполнения сценария установки времени готовки",
            order_id=data.order_id,
            chat_id=data.chat_id,
            cooking_time_minutes=data.cooking_time_minutes
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_chat_id(data.chat_id)
        if not warehouse:
            logger.error(
                "Склад не найден при установке времени готовки",
                chat_id=data.chat_id,
                order_id=data.order_id
            )
            raise WarehouseNotFoundException(f"Склад не привязан к чату {data.chat_id}")
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            logger.error(
                "Заказ не найден при установке времени готовки",
                order_id=data.order_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит складу
        if order.warehouse_id != warehouse.uid:
            logger.error(
                "Попытка установить время готовки для чужого заказа",
                order_id=data.order_id,
                order_warehouse_id=order.warehouse_id,
                warehouse_uid=warehouse.uid
            )
            raise OrderNotFoundException(f"Заказ не принадлежит складу {warehouse.uid}")
            
        # Проверка, что заказ в подходящем статусе
        if order.status != OrderStatus.ACCEPTED_BY_PARTNER:
            logger.warning(
                "Попытка установить время готовки для заказа в неподходящем статусе",
                order_id=data.order_id,
                current_status=order.status.value
            )
            # Если заказ уже в статусе готовки - возвращаем его
            if order.status == OrderStatus.COOKING:
                logger.info(
                    "Заказ уже в статусе готовки, возврат текущего состояния",
                    order_id=data.order_id
                )
                return order
                
            raise OrderAlreadyCompletedException(
                f"Невозможно установить время готовки для заказа со статусом: {order.status.value}"
            )
            
        # Установка времени готовки
        try:
            updated_order = await self.order_service.set_cooking_time(
                order=order,
                cooking_time_minutes=data.cooking_time_minutes
            )
            
            logger.info(
                "Время готовки успешно установлено",
                order_id=updated_order.id,
                cooking_time_minutes=data.cooking_time_minutes,
                expected_ready_at=updated_order.expected_ready_at
            )
            
            return updated_order
            
        except Exception as e:
            logger.error(
                "Ошибка при установке времени готовки",
                order_id=data.order_id,
                error=str(e),
                exc_info=True
            )
            raise


class ConfirmReadyUseCase:
    """
    Use case для подтверждения готовности заказа.
    
    Отвечает за:
    - Проверку, что заказ принадлежит складу
    - Обновление статуса заказа на 'ready_for_delivery'
    - Сохранение фото заказа
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        warehouse_repository: WarehouseRepository,
        order_service: OrderService,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        
    async def execute(self, data: ConfirmReadyDTO) -> Order:
        """
        Выполняет сценарий подтверждения готовности заказа.
        
        Args:
            data: DTO с данными для подтверждения готовности
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
        """
        logger.info(
            "Начало выполнения сценария подтверждения готовности заказа",
            order_id=data.order_id,
            chat_id=data.chat_id,
            photo_count=len(data.photo_file_ids)
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_chat_id(data.chat_id)
        if not warehouse:
            logger.error(
                "Склад не найден при подтверждении готовности",
                chat_id=data.chat_id,
                order_id=data.order_id
            )
            raise WarehouseNotFoundException(f"Склад не привязан к чату {data.chat_id}")
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            logger.error(
                "Заказ не найден при подтверждении готовности",
                order_id=data.order_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит складу
        if order.warehouse_id != warehouse.uid:
            logger.error(
                "Попытка подтвердить готовность чужого заказа",
                order_id=data.order_id,
                order_warehouse_id=order.warehouse_id,
                warehouse_uid=warehouse.uid
            )
            raise OrderNotFoundException(f"Заказ не принадлежит складу {warehouse.uid}")
            
        # Проверка, что заказ в подходящем статусе
        if order.status != OrderStatus.COOKING:
            logger.warning(
                "Попытка подтвердить готовность для заказа в неподходящем статусе",
                order_id=data.order_id,
                current_status=order.status.value
            )
            # Если заказ уже в статусе готов к доставке - возвращаем его
            if order.status == OrderStatus.READY_FOR_DELIVERY:
                logger.info(
                    "Заказ уже в статусе готов к доставке, возврат текущего состояния",
                    order_id=data.order_id
                )
                return order
                
            raise OrderAlreadyCompletedException(
                f"Невозможно подтвердить готовность для заказа со статусом: {order.status.value}"
            )
            
        # Подтверждение готовности заказа
        try:
            updated_order = await self.order_service.confirm_ready(
                order=order,
                photo_file_ids=data.photo_file_ids
            )
            
            logger.info(
                "Готовность заказа успешно подтверждена",
                order_id=updated_order.id,
                photo_count=len(data.photo_file_ids)
            )
            
            return updated_order
            
        except Exception as e:
            logger.error(
                "Ошибка при подтверждении готовности заказа",
                order_id=data.order_id,
                error=str(e),
                exc_info=True
            )
            raise