from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...domain.entities.order import Order


class ICRMClient(ABC):
    """
    Абстрактный интерфейс клиента CRM системы.

    Определяет контракт для всех операций взаимодействия с CRM:
    - Управление заказами
    - Получение статистики
    - Обновление статусов

    Реализации должны быть асинхронными и выбрасывать IntegrationError
    при сбоях интеграции.
    """

    @abstractmethod
    async def update_order_status(
            self,
            order_id: str,
            status: str,
            cooking_time_minutes: Optional[int] = None,
            photos: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Обновляет статус заказа в CRM.

        Args:
            order_id: Идентификатор заказа в CRM
            status: Новый статус заказа
            cooking_time_minutes: Время приготовления в минутах (опционально)
            photos: Список фотографий (формат зависит от реализации CRM)

        Returns:
            Ответ CRM в виде словаря

        Raises:
            IntegrationError: При ошибке обновления
        """
        ...

    @abstractmethod
    async def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Получает полные детали заказа по его ID.

        Args:
            order_id: Идентификатор заказа в CRM

        Returns:
            Данные заказа в виде словаря

        Raises:
            IntegrationError: При ошибке получения данных
        """
        ...

    @abstractmethod
    async def get_sales_statistics(
            self,
            warehouse_id: str,
            date_from: str,
            date_to: str,
            statuses: List[str]
    ) -> Dict[str, Any]:
        """
        Получает агрегированную статистику продаж за период.

        Args:
            warehouse_id: Идентификатор склада
            date_from: Начало периода (ISO 8601, UTC)
            date_to: Конец периода (ISO 8601, UTC)
            statuses: Список статусов заказов для учёта

        Returns:
            Статистика продаж (структура зависит от CRM)

        Raises:
            IntegrationError: При ошибке получения статистики
        """
        ...

    @abstractmethod
    async def send_new_order(self, order: Order) -> Dict[str, Any]:
        """
        Регистрирует новый заказ в CRM.

        Args:
            order: Объект заказа из домена

        Returns:
            Ответ CRM (обычно с подтверждённым ID заказа)

        Raises:
            IntegrationError: При ошибке отправки заказа
        """
        ...

    @abstractmethod
    async def add_order_photo(self, order_id: str, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Добавляет фотографию к заказу в CRM.

        Args:
            order_id: Идентификатор заказа в CRM
            photo_data: Данные фотографии (формат зависит от реализации CRM)

        Returns:
            Ответ CRM в виде словаря

        Raises:
            IntegrationError: При ошибке добавления фото
        """
        ...