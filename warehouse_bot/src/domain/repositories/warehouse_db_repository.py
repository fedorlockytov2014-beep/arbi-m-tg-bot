from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.warehouse import Warehouse


class IWarehouseDBRepository(ABC):
    """
    Абстрактный репозиторий для работы со складами из базы данных.
    """

    @abstractmethod
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        """
        Получает из БД склад по ID.

        Args:
            warehouse_id: ID склада

        Returns:
            Warehouse: Склад или None если не найден
        """
        ...

    @abstractmethod
    async def get_by_telegram_chat_id(self, chat_id: int) -> Optional[Warehouse]:
        """
        Получает из БД склад по ID Telegram-чата.

        Args:
            chat_id: ID Telegram-чата

        Returns:
            Warehouse: Склад или None если не найден
        """
        ...

    @abstractmethod
    async def get_all(self) -> List[Warehouse]:
        """
        Получает из БД  все склады.

        Returns:
            List[Warehouse]: Список складов
        """
        ...

    @abstractmethod
    async def save(self, warehouse: Warehouse) -> Warehouse:
        """
        Сохраняет в БД склад.

        Args:
            warehouse: Склад для сохранения

        Returns:
            Warehouse: Сохранённый склад
        """
        ...

    @abstractmethod
    async def update(self, warehouse: Warehouse) -> Warehouse:
        """
        Обновляет в БД  склад.

        Args:
            warehouse: Склад для обновления

        Returns:
            Warehouse: Обновлённый склад
        """
        ...

    @abstractmethod
    async def delete(self, warehouse_id: str) -> bool:
        """
        Удаляет в БД склад.

        Args:
            warehouse_id: ID склада для удаления

        Returns:
            bool: True если склад был удалён, иначе False
        """
        ...

    @abstractmethod
    async def find_by_activation_code(self, activation_code: str) -> Optional[Warehouse]:
        """
        Находит склад по коду активации из БД .

        Args:
            activation_code: Код активации

        Returns:
            Warehouse: Склад или None если не найден
        """
        ...

    @abstractmethod
    async def deactivate_by_telegram_chat_id(self, chat_id: int) -> bool:
        """
        Деактивирует склад по ID Telegram-чата из БД .

        Args:
            chat_id: ID Telegram-чата

        Returns:
            bool: True если деактивация прошла успешно
        """
        ...