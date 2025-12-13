from datetime import datetime

from ...application.dto.incoming_orders import AcceptOrderDTO, SetCookingTimeDTO, CancelOrderDTO, AddOrderPhotoDTO, MarkOrderReadyWithPhotosDTO
from ...application.exceptions import (
    OrderAlreadyAcceptedException,
    OrderNotFoundException,
    WarehouseNotFoundException
)
from ...domain.entities.order import Order
from ...domain.repositories.crm_repository import ICRMClient
from ...domain.repositories.order_repository import IOrderRepository
from ...domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ...domain.repositories.warehouse_repository import IWarehouseRepository
from ...domain.services.order_service import OrderService
from ...domain.value_objects.cooking_time import CookingTime
from ...domain.value_objects.order_status import OrderStatus
from ...infrastructure.logging.utils import get_logger

logger = get_logger(__name__)

class AcceptOrderUseCase:
    """
    Use case для принятия заказа партнером.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку, что заказ еще не принят другим партнером
    - Обновление статуса заказа
    - Сохранение времени принятия заказа
    - Интеграцию с CRM системой
    
    Атрибуты:
        order_repository: Репозиторий для работы с заказами
        warehouse_repository: Репозиторий для работы со складами
        order_service: Сервис для бизнес-логики заказов
        crm_client: Клиент для интеграции с CRM
    """
    
    def __init__(
        self,
        order_repository: IOrderRepository,
        warehouse_repository: IWarehouseRepository,
        warehouse_db_repository: IWarehouseDBRepository,
        order_service: OrderService,
        crm_client: ICRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
            crm_client: Клиент для интеграции с CRM
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.order_service = order_service
        self.crm_client = crm_client
        
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
        await logger.info(
            "Начало выполнения сценария принятия заказа",
            order_id=data.order_id,
            chat_id=data.chat_id,
            warehouse_id=data.warehouse_id
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_db_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при попытке принять заказ",
                warehouse_id=data.warehouse_id,
                order_id=data.order_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка принять заказ для чужого склада",
                warehouse_id=data.warehouse_id,
                chat_id=data.chat_id,
                warehouse_chat_id=warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        await logger.debug("Заказ получен из CRM", order=order)
        if not order:
            await logger.error(
                "Заказ не найден при попытке принять",
                order_id=data.order_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ еще не принят
        if order.status in [
            OrderStatus.ACCEPTED_BY_PARTNER.value, 
            OrderStatus.COOKING.value, 
            OrderStatus.READY_FOR_DELIVERY.value,
            OrderStatus.ON_DELIVERY.value, 
            OrderStatus.DELIVERED.value
        ]:
            await logger.warning(
                "Попытка принять заказ, который уже в работе",
                order_id=data.order_id,
                current_status=order.status.value
            )
            # Если заказ уже принят этим же складом - возвращаем его без ошибки
            if str(order.warehouse_id) == str(data.warehouse_id) and order.status == OrderStatus.ACCEPTED_BY_PARTNER.value:
                await logger.info(
                    "Заказ уже принят этим складом, возврат текущего состояния",
                    order_id=data.order_id
                )
                return order
                
            raise OrderAlreadyAcceptedException(
                f"Заказ уже принят со статусом: {order.status.value}"
            )
            
        # Проверка, что заказ относится к этому складу
        if int(order.warehouse_id) != int(data.warehouse_id):
            await logger.error(
                "Попытка принять заказ, не относящийся к складу",
                order_id=data.order_id,
                order_warehouse_id=order.warehouse_id,
                target_warehouse_id=data.warehouse_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не относится к складу {data.warehouse_id}")
            
        # Обновление статуса заказа
        try:
            updated_order = await self.order_service.accept_order(
                order=order,
                accepted_at=datetime.utcnow()
            )
            
            # Сохраняем обновленный заказ
            result = await self.order_repository.update(updated_order)
            
            # Интеграция с CRM: обновляем статус заказа в CRM системе
            try:
                async with self.crm_client as crm:
                    await crm.update_order_status(
                        order_id=data.order_id,
                        status=OrderStatus.ACCEPTED_BY_PARTNER.value  # Это соответствует 'Принят партнером'
                    )
                    
                await logger.info(
                    "Статус заказа успешно обновлен в CRM системе",
                    order_id=result.id,
                    new_status=OrderStatus.ACCEPTED_BY_PARTNER.value
                )
            except Exception as e:
                await logger.error(
                    "Ошибка при обновлении статуса заказа в CRM системе",
                    order_id=result.id,
                    error=str(e)
                )
                # Не прерываем выполнение, так как локальное обновление прошло успешно
                
            await logger.info(
                "Заказ успешно принят",
                order_id=result.id,
                warehouse_id=result.warehouse_id,
                accepted_at=result.accepted_at
            )
            
            return result
            
        except Exception as e:
            await logger.error(
                "Ошибка при принятии заказа",
                order_id=data.order_id,
                error=str(e)
            )
            raise


class CancelOrderUseCase:
    """
    Use case для отмены заказа.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку прав доступа к заказу
    - Отмену заказа
    - Обновление статуса заказа на "CANCELLED"
    - Интеграцию с CRM системой
    """
    
    def __init__(
        self,
        order_repository: IOrderRepository,
        warehouse_repository: IWarehouseRepository,
        order_service: OrderService,
        crm_client: ICRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
            crm_client: Клиент для интеграции с CRM
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        self.crm_client = crm_client
        
    async def execute(self, data: CancelOrderDTO) -> Order:
        """
        Выполняет сценарий отмены заказа.
        
        Args:
            data: DTO с данными для отмены заказа
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
            InvalidOrderStatusException: Если заказ в недопустимом статусе
        """
        await logger.info(
            "Начало выполнения сценария отмены заказа",
            order_id=data.order_id,
            chat_id=data.chat_id,
            warehouse_id=data.warehouse_id
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при отмене заказа",
                warehouse_id=data.warehouse_id,
                order_id=data.order_id
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка отменить заказ для чужого склада",
                warehouse_id=data.warehouse_id,
                chat_id=data.chat_id,
                warehouse_chat_id=warehouse.telegram_chat_id
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            await logger.error(
                "Заказ не найден при отмене",
                order_id=data.order_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит этому складу
        if order.warehouse_id != data.warehouse_id:
            await logger.error(
                "Попытка отменить чужой заказ",
                order_id=data.order_id,
                order_warehouse_id=order.warehouse_id,
                target_warehouse_id=data.warehouse_id
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не принадлежит складу {data.warehouse_id}")
            
        # Проверка статуса заказа - можно отменить только если не доставлен и не отменен
        if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
            await logger.error(
                "Невозможно отменить заказ в текущем статусе",
                order_id=data.order_id,
                current_status=order.status.value
            )
            raise OrderAlreadyAcceptedException(
                f"Невозможно отменить заказ со статусом {order.status.value}"
            )
            
        # Отмена заказа
        try:
            updated_order = await self.order_service.cancel_order(
                order=order
            )
            
            # Сохраняем обновленный заказ
            result = await self.order_repository.update(updated_order)
            
            # Интеграция с CRM: обновляем статус заказа в CRM системе
            try:
                async with self.crm_client as crm:
                    await crm.update_order_status(
                        order_id=data.order_id,
                        status="cancelled"  # Это соответствует отмененному заказу
                    )
                    
                await logger.info(
                    "Статус заказа успешно обновлен в CRM системе",
                    order_id=result.id,
                    new_status="cancelled"
                )
            except Exception as e:
                await logger.error(
                    "Ошибка при обновлении статуса заказа в CRM системе",
                    order_id=result.id,
                    error=str(e)
                )
                # Не прерываем выполнение, так как локальное обновление прошло успешно
            
            await logger.info(
                "Заказ успешно отменен",
                order_id=result.id,
                warehouse_id=result.warehouse_id,
                previous_status=order.status.value,
                new_status=result.status.value
            )
            
            return result
            
        except Exception as e:
            await logger.error(
                "Ошибка при отмене заказа",
                order_id=data.order_id,
                error=str(e)
            )
            raise


class SetCookingTimeUseCase:
    """
    Use case для установки времени приготовления заказа.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку прав доступа к заказу
    - Установку времени приготовления
    - Обновление статуса заказа на "COOKING"
    - Интеграцию с CRM системой
    """
    
    def __init__(
        self,
        order_repository: IOrderRepository,
        warehouse_repository: IWarehouseRepository,
        order_service: OrderService,
        crm_client: ICRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
            crm_client: Клиент для интеграции с CRM
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        self.crm_client = crm_client
        
    async def execute(self, data: SetCookingTimeDTO) -> Order:
        """
        Выполняет сценарий установки времени приготовления.
        
        Args:
            data: DTO с данными для установки времени приготовления
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
            InvalidOrderStatusException: Если заказ в недопустимом статусе
        """
        await logger.info(
            "Начало выполнения сценария установки времени приготовления",
            order_id=data.order_id,
            chat_id=data.chat_id,
            warehouse_id=data.warehouse_id,
            cooking_time_minutes=data.cooking_time_minutes
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при установке времени приготовления",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "order_id": data.order_id
                }
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка установить время приготовления для чужого склада",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            await logger.error(
                "Заказ не найден при установке времени приготовления",
                extra={
                    "order_id": data.order_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит этому складу
        if order.warehouse_id != data.warehouse_id:
            await logger.error(
                "Попытка установить время приготовления для чужого заказа",
                extra={
                    "order_id": data.order_id,
                    "order_warehouse_id": order.warehouse_id,
                    "target_warehouse_id": data.warehouse_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не принадлежит складу {data.warehouse_id}")
            
        # Проверка статуса заказа
        if order.status not in [OrderStatus.ACCEPTED_BY_PARTNER, OrderStatus.COOKING]:
            await logger.error(
                "Невозможно установить время приготовления для заказа в текущем статусе",
                extra={
                    "order_id": data.order_id,
                    "current_status": order.status.value
                }
            )
            raise OrderAlreadyAcceptedException(
                f"Невозможно установить время приготовления для заказа со статусом {order.status.value}"
            )
            
        # Валидация времени приготовления
        if data.cooking_time_minutes <= 0 or data.cooking_time_minutes > 180:
            await logger.error(
                "Неверное время приготовления",
                extra={
                    "order_id": data.order_id,
                    "cooking_time_minutes": data.cooking_time_minutes
                }
            )
            raise ValueError("Время приготовления должно быть от 1 до 180 минут")
            
        # Создание объекта CookingTime
        cooking_time = CookingTime(minutes=data.cooking_time_minutes)
        
        # Установка времени приготовления
        try:
            updated_order = await self.order_service.set_cooking_time(
                order=order,
                cooking_time=cooking_time
            )
            
            # Сохраняем обновленный заказ
            result = await self.order_repository.update(updated_order)
            
            # Интеграция с CRM: обновляем статус и время приготовления в CRM системе
            try:
                async with self.crm_client as crm:
                    await crm.update_order_status(
                        order_id=data.order_id,
                        status=OrderStatus.COOKING.value,  # Это соответствует 'Готовится'
                        cooking_time_minutes=data.cooking_time_minutes,
                        expected_ready_at=updated_order.expected_ready_at.isoformat() if updated_order.expected_ready_at else None
                    )
                    
                await logger.info(
                    "Статус заказа и время приготовления успешно обновлены в CRM системе",
                    extra={
                        "order_id": result.id,
                        "new_status": OrderStatus.COOKING.value,
                        "cooking_time_minutes": data.cooking_time_minutes
                    }
                )
            except Exception as e:
                await logger.error(
                    "Ошибка при обновлении статуса заказа в CRM системе",
                    order_id=result.id,
                    error=str(e)
                )
                # Не прерываем выполнение, так как локальное обновление прошло успешно
            
            await logger.info(
                "Время приготовления успешно установлено",
                order_id=result.id,
                cooking_time_minutes=result.cooking_time_minutes,
                expected_ready_at=result.expected_ready_at
            )
            
            return result
            
        except Exception as e:
            await logger.error(
                "Ошибка при установке времени приготовления",
                extra={
                    "order_id": data.order_id,
                    "error": str(e),
                    "exc_info": True
                }
            )


class MarkOrderReadyWithPhotosUseCase:
    """
    Use case для подтверждения готовности заказа с фотографиями.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку прав доступа к заказу
    - Подтверждение готовности заказа
    - Обновление статуса заказа на "READY_FOR_DELIVERY"
    - Сохранение фотографий заказа
    - Интеграцию с CRM системой
    """

    def __init__(
        self,
        order_repository: IOrderRepository,
        warehouse_repository: IWarehouseRepository,
        order_service: OrderService,
        crm_client: ICRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
            crm_client: Клиент для интеграции с CRM
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        self.crm_client = crm_client
        
    async def execute(self, data: MarkOrderReadyWithPhotosDTO) -> Order:
        """
        Выполняет сценарий подтверждения готовности заказа с фотографиями.
        
        Args:
            data: DTO с данными для подтверждения готовности заказа
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
            InvalidOrderStatusException: Если заказ в недопустимом статусе
        """
        await logger.info(
            "Начало выполнения сценария подтверждения готовности заказа",
            extra={
                "order_id": data.order_id,
                "chat_id": data.chat_id,
                "warehouse_id": data.warehouse_id
            }
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при подтверждении готовности заказа",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "order_id": data.order_id
                }
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка подтвердить готовность заказа для чужого склада",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            await logger.error(
                "Заказ не найден при подтверждении готовности",
                extra={
                    "order_id": data.order_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит этому складу
        if order.warehouse_id != data.warehouse_id:
            await logger.error(
                "Попытка подтвердить готовность чужого заказа",
                extra={
                    "order_id": data.order_id,
                    "order_warehouse_id": order.warehouse_id,
                    "target_warehouse_id": data.warehouse_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не принадлежит складу {data.warehouse_id}")
            
        # Проверка статуса заказа - заказ должен быть в статусе COOKING
        if order.status != OrderStatus.COOKING:
            await logger.error(
                "Невозможно подтвердить готовность заказа в текущем статусе",
                extra={
                    "order_id": data.order_id,
                    "current_status": order.status.value
                }
            )
            raise OrderAlreadyAcceptedException(
                f"Невозможно подтвердить готовность заказа со статусом {order.status.value}"
            )
            
        # Подтверждение готовности заказа
        try:
            updated_order = await self.order_service.mark_as_ready_for_delivery(
                order=order,
                ready_at=datetime.utcnow()
            )
            
            # Сохраняем обновленный заказ
            result = await self.order_repository.update(updated_order)
            
            # Интеграция с CRM: обновляем статус заказа в CRM системе
            try:
                async with self.crm_client as crm:
                    # Подготовим данные для передачи фото в CRM
                    photos_data = []
                    for photo_url in data.photo_urls:
                        photos_data.append({
                            "telegram_file_id": photo_url
                        })
                    
                    await crm.update_order_status(
                        order_id=data.order_id,
                        status=OrderStatus.READY_FOR_DELIVERY.value,
                        photos=photos_data if photos_data else None
                    )
                    
                await logger.info(
                    "Статус заказа успешно обновлен в CRM системе",
                    extra={
                        "order_id": result.id,
                        "new_status": OrderStatus.READY_FOR_DELIVERY.value
                    }
                )
            except Exception as e:
                await logger.error(
                    "Ошибка при обновлении статуса заказа в CRM системе",
                    order_id=result.id,
                    error=str(e)
                )
                # Не прерываем выполнение, так как локальное обновление прошло успешно
            
            await logger.info(
                "Заказ успешно отмечен как готов к доставке",
                order_id=result.id,
                warehouse_id=result.warehouse_id,
                ready_at=result.ready_at
            )
            
            return result
            
        except Exception as e:
            await logger.error(
                "Ошибка при подтверждении готовности заказа",
                extra={
                    "order_id": data.order_id,
                    "error": str(e),
                    "exc_info": True
                }
            )
            raise


class AddOrderPhotoUseCase:
    """
    Use case для добавления фотографии к заказу.
    
    Отвечает за:
    - Проверку существования заказа
    - Проверку прав доступа к заказу
    - Добавление фотографии к заказу
    - Интеграцию с CRM системой
    """

    def __init__(
        self,
        order_repository: IOrderRepository,
        warehouse_repository: IWarehouseRepository,
        order_service: OrderService,
        crm_client: ICRMClient,
    ):
        """
        Инициализирует use case.
        
        Args:
            order_repository: Репозиторий для работы с заказами
            warehouse_repository: Репозиторий для работы со складами
            order_service: Сервис для бизнес-логики заказов
            crm_client: Клиент для интеграции с CRM
        """
        self.order_repository = order_repository
        self.warehouse_repository = warehouse_repository
        self.order_service = order_service
        self.crm_client = crm_client
        
    async def execute(self, data: AddOrderPhotoDTO) -> Order:
        """
        Выполняет сценарий добавления фотографии к заказу.
        
        Args:
            data: DTO с данными для добавления фотографии
            
        Returns:
            Order: Обновленный заказ
            
        Raises:
            OrderNotFoundException: Если заказ не найден
            WarehouseNotFoundException: Если склад не найден
        """
        await logger.info(
            "Начало выполнения сценария добавления фотографии к заказу",
            extra={
                "order_id": data.order_id,
                "chat_id": data.chat_id,
                "warehouse_id": data.warehouse_id
            }
        )
        
        # Проверка, что склад существует и привязан к чату
        warehouse = await self.warehouse_repository.get_by_id(data.warehouse_id)
        if not warehouse:
            await logger.error(
                "Склад не найден при добавлении фото к заказу",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "order_id": data.order_id
                }
            )
            raise WarehouseNotFoundException(f"Склад с ID {data.warehouse_id} не найден")
            
        if warehouse.telegram_chat_id != data.chat_id:
            await logger.error(
                "Попытка добавить фото к заказу для чужого склада",
                extra={
                    "warehouse_id": data.warehouse_id,
                    "chat_id": data.chat_id,
                    "warehouse_chat_id": warehouse.telegram_chat_id
                }
            )
            raise WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} не привязан к данному чату"
            )
            
        # Получение заказа
        order = await self.order_repository.get_by_id(data.order_id)
        if not order:
            await logger.error(
                "Заказ не найден при добавлении фото",
                extra={
                    "order_id": data.order_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не найден")
            
        # Проверка, что заказ принадлежит этому складу
        if order.warehouse_id != data.warehouse_id:
            await logger.error(
                "Попытка добавить фото к чужому заказу",
                extra={
                    "order_id": data.order_id,
                    "order_warehouse_id": order.warehouse_id,
                    "target_warehouse_id": data.warehouse_id
                }
            )
            raise OrderNotFoundException(f"Заказ с ID {data.order_id} не принадлежит складу {data.warehouse_id}")
            
        # Добавление фотографии к заказу
        try:
            # Интеграция с CRM: добавляем фото в CRM систему
            try:
                photo_data = {
                    "telegram_file_id": data.photo_url
                }
                
                async with self.crm_client as crm:
                    await crm.add_order_photo(
                        order_id=data.order_id,
                        photo_data=photo_data
                    )
                    
                await logger.info(
                    "Фото успешно добавлено к заказу в CRM системе",
                    extra={
                        "order_id": data.order_id,
                        "photo_id": photo_data['telegram_file_id']
                    }
                )
            except Exception as e:
                await logger.error(
                    "Ошибка при добавлении фото к заказу в CRM системе",
                    order_id=data.order_id,
                    error=str(e)
                )
                # Не прерываем выполнение, так как фото может быть сохранено локально
            
            await logger.info(
                "Фото успешно добавлено к заказу",
                order_id=order.id,
                warehouse_id=order.warehouse_id,
                photo_id=data.photo_url
            )
            
            return order
            
        except Exception as e:
            await logger.error(
                "Ошибка при добавлении фото к заказу",
                extra={
                    "order_id": data.order_id,
                    "error": str(e),
                    "exc_info": True
                }
            )
            raise