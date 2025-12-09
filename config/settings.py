import os
from dataclasses import dataclass
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field


class TelegramConfig(BaseModel):
    bot_token: str = Field(..., description="Токен Telegram бота")
    max_connections: int = Field(default=100, description="Максимальное количество одновременных обновлений")
    polling_timeout: int = Field(default=30, description="Таймаут для Long Polling")
    
    class WebhookConfig(BaseModel):
        enabled: bool = Field(default=True, description="Включить/выключить вебхуки")
        url: str = Field(default="https://your-domain.com/webhook", description="URL для вебхука")
        cert_path: Optional[str] = Field(default=None, description="Путь к SSL сертификату")
        port: int = Field(default=8443, description="Порт для вебхука")
    
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)


class DatabaseConfig(BaseModel):
    url: str = Field(default="postgresql+asyncpg://user:password@localhost:5432/warehouse_bot", description="URL подключения к БД")
    echo_sql: bool = Field(default=False, description="Включить логирование SQL запросов")
    max_connections: int = Field(default=20, description="Максимальное количество соединений в пуле")
    query_timeout: int = Field(default=30, description="Таймаут запросов к БД")


class CacheConfig(BaseModel):
    enabled: bool = Field(default=True, description="Включить/выключить кеширование")
    redis_url: str = Field(default="redis://localhost:6379/0", description="URL подключения к Redis")
    
    class TTLConfig(BaseModel):
        stats_today: int = Field(default=60, description="TTL для статистики за сегодня")
        stats_week: int = Field(default=60, description="TTL для статистики за неделю")
        stats_month: int = Field(default=900, description="TTL для статистики за месяц")
        warehouse_data: int = Field(default=3600, description="TTL для данных о складе")
    
    ttl: TTLConfig = Field(default_factory=TTLConfig)
    max_items: int = Field(default=10000, description="Максимальное количество элементов в кеше")


class CRMConfig(BaseModel):
    base_url: str = Field(default="https://your-crm.com/api/v1", description="Базовый URL API CRM")
    api_token: str = Field(default="YOUR_CRM_API_TOKEN", description="Токен авторизации CRM")
    timeout: int = Field(default=15, description="Таймаут для запросов к API CRM")
    max_retries: int = Field(default=3, description="Максимальное количество попыток")
    retry_delay: int = Field(default=2, description="Задержка между повторными попытками")
    no_retry_statuses: List[int] = Field(default=[400, 401, 403, 404], description="Коды статусов без повтора")


class PhotoStorageConfig(BaseModel):
    type: str = Field(default="TELEGRAM", description="Тип хранилища фотографий")
    
    class S3Config(BaseModel):
        bucket_name: str = Field(default="warehouse-orders-photos", description="Имя бакета S3")
        region: str = Field(default="eu-central-1", description="Регион S3")
        access_key: str = Field(default="YOUR_ACCESS_KEY", description="Ключ доступа S3")
        secret_key: str = Field(default="YOUR_SECRET_KEY", description="Секретный ключ S3")
        endpoint_url: Optional[str] = Field(default=None, description="URL для совместимых с S3 сервисов")
    
    s3: S3Config = Field(default_factory=S3Config)
    
    class LocalConfig(BaseModel):
        storage_path: str = Field(default="/var/lib/warehouse_bot/photos", description="Путь к локальному хранилищу")
        base_url: str = Field(default="https://your-domain.com/photos/", description="URL для доступа к файлам")
    
    local: LocalConfig = Field(default_factory=LocalConfig)


class SecurityConfig(BaseModel):
    admin_ids: List[int] = Field(default=[123456789, 987654321], description="ID администраторов")
    max_activation_attempts: int = Field(default=3, description="Максимальное количество попыток активации")
    activation_block_time: int = Field(default=15, description="Время блокировки после попыток")
    max_photos_per_order: int = Field(default=3, description="Максимальное количество фото на заказ")
    max_cooking_time_minutes: int = Field(default=180, description="Максимальное время приготовления")


class WebhookConfig(BaseModel):
    secret_key: str = Field(default="your-webhook-secret-key-here", description="Секретный ключ для вебхуков")


class StatisticsConfig(BaseModel):
    included_statuses: List[str] = Field(
        default=["ready_for_delivery", "on_delivery", "delivered"],
        description="Статусы заказов, учитываемые в статистике"
    )
    excluded_statuses: List[str] = Field(
        default=["cancelled", "new", "sent_to_partner", "accepted_by_partner", "cooking"],
        description="Статусы заказов, не учитываемые в статистике"
    )
    max_period_days: int = Field(default=365, description="Максимальный период для статистики")


class BotMenuConfig(BaseModel):
    enabled: bool = Field(default=True, description="Включить/выключить меню бота")
    items: List[dict] = Field(
        default=[
            {"command": "start", "description": "Перезапуск бота"},
            {"command": "stats", "description": "📊 Статистика продаж"},
            {"command": "help", "description": "Помощь и поддержка"}
        ],
        description="Элементы меню бота"
    )


class Settings(BaseModel):
    log_level: str = Field(default="INFO", description="Уровень логирования")
    log_format: str = Field(default="JSON", description="Формат логов")
    app_version: str = Field(default="1.0.0", description="Версия приложения")
    
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    crm: CRMConfig = Field(default_factory=CRMConfig)
    photo_storage: PhotoStorageConfig = Field(default_factory=PhotoStorageConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    statistics: StatisticsConfig = Field(default_factory=StatisticsConfig)
    bot_menu: BotMenuConfig = Field(default_factory=BotMenuConfig)


def load_config(config_path: str = "/workspace/config/config.yaml") -> Settings:
    """
    Загружает конфигурацию из YAML файла.
    
    Args:
        config_path: Путь к конфигурационному файлу
        
    Returns:
        Settings: Объект настроек
    """
    with open(config_path, 'r', encoding='utf-8') as file:
        config_data = yaml.safe_load(file)
    
    # Обновляем настройки переменными окружения, если они заданы
    if os.getenv('TELEGRAM_BOT_TOKEN'):
        config_data['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if os.getenv('DATABASE_URL'):
        config_data['database']['url'] = os.getenv('DATABASE_URL')
    
    if os.getenv('CRM_API_TOKEN'):
        config_data['crm']['api_token'] = os.getenv('CRM_API_TOKEN')
    
    if os.getenv('WEBHOOK_SECRET_KEY'):
        config_data['webhook']['secret_key'] = os.getenv('WEBHOOK_SECRET_KEY')
    
    return Settings(**config_data)


# Глобальный экземпляр настроек
settings = load_config()