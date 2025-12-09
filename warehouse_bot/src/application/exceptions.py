"""
Модуль содержит пользовательские исключения приложения.
"""


class ApplicationError(Exception):
    """
    Базовое исключение приложения.
    """
    pass


class IntegrationError(ApplicationError):
    """
    Исключение для ошибок интеграции с внешними сервисами.
    
    Attributes:
        status_code: HTTP статус код (если применимо)
    """
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class OrderNotFoundException(ApplicationError):
    """
    Исключение, выбрасываемое когда заказ не найден.
    """
    pass


class WarehouseNotFoundException(ApplicationError):
    """
    Исключение, выбрасываемое когда склад не найден.
    """
    pass


class PartnerNotFoundException(ApplicationError):
    """
    Исключение, выбрасываемое когда партнёр не найден.
    """
    pass


class OrderAlreadyAcceptedException(ApplicationError):
    """
    Исключение, выбрасываемое когда заказ уже принят другим партнёром.
    """
    pass


class OrderAlreadyCompletedException(ApplicationError):
    """
    Исключение, выбрасываемое когда заказ уже завершён.
    """
    pass


class InvalidOrderStatusException(ApplicationError):
    """
    Исключение, выбрасываемое когда статус заказа недействителен.
    """
    pass


class InvalidCookingTimeException(ApplicationError):
    """
    Исключение, выбрасываемое когда время приготовления недействительно.
    """
    pass


class ActivationCodeNotFoundException(ApplicationError):
    """
    Исключение, выбрасываемое когда код активации не найден.
    """
    pass


class InvalidActivationCodeException(ApplicationError):
    """
    Исключение, выбрасываемое когда код активации недействителен.
    """
    pass


class MaxActivationAttemptsExceededException(ApplicationError):
    """
    Исключение, выбрасываемое когда превышено максимальное количество попыток активации.
    """
    pass


class StatisticsCalculationError(ApplicationError):
    """
    Исключение, выбрасываемое при ошибках расчета статистики.
    """
    pass


class PhotoUploadError(ApplicationError):
    """
    Исключение, выбрасываемое при ошибках загрузки фотографий.
    """
    pass