from ...application.dto.incoming_orders import ActivateWarehouseDTO
from ...application.exceptions import (
    InvalidActivationCodeException,
    WarehouseNotFoundException
)
from ...domain.entities import Warehouse
from ...domain.repositories.warehouse_db_repository import IWarehouseDBRepository
from ...domain.repositories.warehouse_repository import IWarehouseRepository
from ...infrastructure.logging import get_logger, log_user_action, log_server_action, log_error, log_warning
from ...infrastructure.integrations.crm_client import CRMClient

logger = get_logger(__name__)


class ActivateWarehouseUseCase:
    """
    Use case для активации склада.

    Отвечает за:
    - Проверку данных склада через CRM
    - Привязку склада к Telegram-чату в локальной базе
    - Управление попытками активации
    """

    def __init__(
            self,
            warehouse_repository: IWarehouseRepository,
            warehouse_db_repository: IWarehouseDBRepository,
            crm_client: CRMClient,
    ):
        """
        Инициализирует use case.

        Args:
            warehouse_repository: Репозиторий для работы с данными склада (можно удалить, если не используется)
            warehouse_db_repository: Репозиторий для сохранения/чтения складов из локальной БД
            crm_client: Клиент для взаимодействия с CRM
        """
        self.warehouse_repository = warehouse_repository
        self.warehouse_db_repository = warehouse_db_repository
        self.crm_client = crm_client

    async def execute(self, data: ActivateWarehouseDTO) -> bool:
        """
        Выполняет сценарий активации склада.

        Args:
            data: DTO с данными для активации склада

        Returns:
            bool: True если активация прошла успешно

        Raises:
            WarehouseNotFoundException: Если склад не найден в CRM или уже привязан к другому чату
            InvalidActivationCodeException: Если код активации недействителен или не соответствует складу
        """
        # 1. Логируем попытку активации
        await self._log_activation_attempt(data)

        # 2. Взаимодействуем с CRM: валидация склада и кода активации
        async with self.crm_client as client:
            # 2.1 Проверяем существование склада в CRM
            crm_warehouse_data = await self._validate_warehouse_in_crm(client, data.warehouse_id)

            # 2.2 Если передан код активации — проверяем его в CRM и соотнесение со складом
            await self._validate_activation_code_if_provided(client, data)

            # 3. Получаем или создаём локальное представление склада на основе данных из CRM
            local_warehouse = await self._get_or_create_local_warehouse(data, crm_warehouse_data)

            # 4. Обрабатываем случай, если склад уже активирован
            if local_warehouse.is_active:
                return await self._handle_already_active_warehouse(local_warehouse, data)

            # 5. Активируем склад (привязываем к чату)
            local_warehouse.activate(
                telegram_chat_id=data.chat_id,
                activation_code=data.activation_code
            )

            # 6. Сохраняем или обновляем запись в локальной БД
            await self._save_or_update_warehouse(local_warehouse)

            # 7. Логируем успешную активацию
            await self._log_activation_success(data, local_warehouse.id)

            return True

    async def _log_activation_attempt(self, data: ActivateWarehouseDTO) -> None:
        """
        Логирует попытку активации склада пользователем.

        Args:
            data: DTO с данными активации
        """
        await log_user_action(
            logger,
            user_id=data.chat_id,
            action="warehouse_activation_attempt",
            chat_id=data.chat_id,
            warehouse_id=data.warehouse_id
        )

    async def _validate_warehouse_in_crm(self, client: CRMClient, warehouse_id: str) -> dict:
        """
        Проверяет наличие склада с указанным ID в CRM.

        Args:
            client: Асинхронный клиент CRM
            warehouse_id: ID склада

        Returns:
            dict: Данные склада из CRM

        Raises:
            WarehouseNotFoundException: Если склад не найден в CRM
        """
        response = await client._make_request(
            method="GET",
            endpoint=f"/warehouses/{warehouse_id}",
            expected_status=200
        )
        if "data" not in response or not response["data"]:
            error = WarehouseNotFoundException(f"Склад с ID {warehouse_id} не найден в CRM")
            await log_error(logger, error, context={"warehouse_id": warehouse_id})
            raise error
        return response["data"]

    async def _validate_activation_code_if_provided(self, client: CRMClient, data: ActivateWarehouseDTO) -> None:
        """
        Проверяет код активации в CRM (если он передан в DTO).
        Убеждается, что код действительно принадлежит указанному складу.

        Args:
            client: Асинхронный клиент CRM
            data: DTO с данными активации

        Raises:
            InvalidActivationCodeException: Если код недействителен или не соответствует складу
        """
        if not data.activation_code:
            return

        code_response = await client._make_request(
            method="GET",
            endpoint=f"/warehouses/by-code/{data.activation_code}",
            expected_status=200
        )

        if "data" not in code_response or not code_response["data"]:
            await log_warning(
                logger,
                "Неверный код активации",
                warehouse_id=data.warehouse_id,
                provided_code=data.activation_code,
                chat_id=data.chat_id
            )
            raise InvalidActivationCodeException("Неверный код активации")

        code_warehouses = code_response["data"]
        if isinstance(code_warehouses, list) and len(code_warehouses) > 0:
            code_warehouse = code_warehouses[0]
            if str(code_warehouse.get("id", "")) != data.warehouse_id:
                await log_warning(
                    logger,
                    "Код активации не соответствует складу",
                    warehouse_id=data.warehouse_id,
                    provided_code=data.activation_code,
                    chat_id=data.chat_id
                )
                raise InvalidActivationCodeException("Код активации не соответствует складу")

    async def _get_or_create_local_warehouse(
            self, data: ActivateWarehouseDTO, crm_warehouse_data: dict
    ) -> Warehouse:
        """
        Получает склад из локальной БД или создаёт новую сущность на основе данных из CRM.

        Args:
            data: DTO с данными активации
            crm_warehouse_data: Данные склада, полученные из CRM

        Returns:
            Warehouse: Локальная сущность склада
        """
        local_warehouse = await self.warehouse_db_repository.get_by_id(data.warehouse_id)
        if not local_warehouse:
            from ...domain.entities.warehouse import Warehouse
            local_warehouse = Warehouse(
                id=str(crm_warehouse_data.get("id", data.warehouse_id)),
                name=crm_warehouse_data.get("name", ""),
                address=crm_warehouse_data.get("address", ""),
                telegram_chat_id=None,  # Будет установлен при активации
                activation_code=crm_warehouse_data.get("activation_code") or data.activation_code
            )
        return local_warehouse

    async def _handle_already_active_warehouse(
            self, local_warehouse: Warehouse, data: ActivateWarehouseDTO
    ) -> bool:
        """
        Обрабатывает случай, когда склад уже активирован.
        Если он привязан к тому же чату — возвращает успех.
        Если к другому — выбрасывает исключение.

        Args:
            local_warehouse: Уже активированный склад из БД
            data: DTO с данными активации

        Returns:
            bool: True, если активация не требуется (уже привязан к тому же чату)

        Raises:
            WarehouseNotFoundException: Если склад уже привязан к другому чату
        """
        if local_warehouse.telegram_chat_id == data.chat_id:
            await log_server_action(
                logger,
                action="warehouse_already_activated_same_chat",
                result="success",
                warehouse_id=data.warehouse_id
            )
            return True
        else:
            error = WarehouseNotFoundException(
                f"Склад с ID {data.warehouse_id} уже привязан к другому чату"
            )
            await log_error(
                logger,
                error,
                context={
                    "warehouse_id": data.warehouse_id,
                    "current_chat_id": local_warehouse.telegram_chat_id,
                    "attempted_chat_id": data.chat_id
                }
            )
            raise error

    async def _save_or_update_warehouse(self, warehouse: Warehouse) -> None:
        """
        Сохраняет склад в локальной базе: создаёт новую запись или обновляет существующую.

        Args:
            warehouse: Склад для сохранения
        """
        existing = await self.warehouse_db_repository.get_by_id(warehouse.id)
        if existing:
            await self.warehouse_db_repository.update(warehouse)
        else:
            await self.warehouse_db_repository.save(warehouse)

    async def _log_activation_success(self, data: ActivateWarehouseDTO, warehouse_id: str) -> None:
        """
        Логирует успешную активацию склада.

        Args:
            data: DTO с данными активации
            warehouse_id: ID активированного склада
        """
        await log_user_action(
            logger,
            user_id=data.chat_id,
            action="warehouse_activated_successfully",
            chat_id=data.chat_id,
            warehouse_id=warehouse_id
        )
