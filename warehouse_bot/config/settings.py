import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class TelegramWebhookSettings(BaseModel):
    enabled: bool = True
    url: str = "https://your-domain.com/webhook"
    cert_path: Optional[str] = None
    port: int = 8443


class TelegramSettings(BaseModel):
    bot_token: str = Field(..., description="Telegram bot token from @BotFather")
    max_connections: int = 100
    polling_timeout: int = 30
    webhook: TelegramWebhookSettings = TelegramWebhookSettings()


# class DatabaseSettings(BaseModel):
#     url: str = "postgresql+asyncpg://user:password@localhost:5432/warehouse_bot"
#     echo_sql: bool = False
#     max_connections: int = 20
#     query_timeout: int = 30


class CacheTTLSettings(BaseModel):
    stats_today: int = 60
    stats_week: int = 60
    stats_month: int = 900
    warehouse_data: int = 3600


class CacheSettings(BaseModel):
    enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    ttl: CacheTTLSettings = CacheTTLSettings()
    max_items: int = 10000


class CRMSettings(BaseModel):
    base_url: str = "https://your-crm.com/api/v1"
    api_token: str = "YOUR_CRM_API_TOKEN"
    timeout: int = 15
    max_retries: int = 3
    retry_delay: int = 2
    no_retry_statuses: List[int] = [400, 401, 403, 404]


class S3Settings(BaseModel):
    bucket_name: str = "warehouse-orders-photos"
    region: str = "eu-central-1"
    access_key: str = "YOUR_ACCESS_KEY"
    secret_key: str = "YOUR_SECRET_KEY"
    endpoint_url: Optional[str] = None


class LocalStorageSettings(BaseModel):
    storage_path: str = "/var/lib/warehouse_bot/photos"
    base_url: str = "https://your-domain.com/photos/"


class PhotoStorageSettings(BaseModel):
    type: str = "TELEGRAM"  # TELEGRAM, AWS_S3, LOCAL
    s3: S3Settings = S3Settings()
    local: LocalStorageSettings = LocalStorageSettings()


class WebhookSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    secret_key: str = "your-webhook-secret-key"


class SecuritySettings(BaseModel):
    admin_ids: List[int] = [123456789, 987654321]
    max_activation_attempts: int = 3
    activation_block_time: int = 15
    max_photos_per_order: int = 3
    max_cooking_time_minutes: int = 180


class StatisticsSettings(BaseModel):
    included_statuses: List[str] = ["ready_for_delivery", "on_delivery", "delivered"]
    excluded_statuses: List[str] = ["cancelled", "new", "sent_to_partner", "accepted_by_partner", "cooking"]
    max_period_days: int = 365


class Settings(BaseSettings):
    log_level: str = "INFO"
    log_format: str = "JSON"

    telegram: TelegramSettings
    # database: DatabaseSettings
    cache: CacheSettings
    crm: CRMSettings
    photo_storage: PhotoStorageSettings
    security: SecuritySettings
    statistics: StatisticsSettings
    webhook: WebhookSettings = WebhookSettings()


    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f'log_level must be one of {allowed_levels}')
        return v.upper()

    @field_validator('log_format')
    @classmethod
    def validate_log_format(cls, v):
        allowed_formats = {"JSON", "CONSOLE"}
        if v.upper() not in allowed_formats:
            raise ValueError(f'log_format must be one of {allowed_formats}')
        return v.upper()

    @field_validator('photo_storage')
    @classmethod
    def validate_photo_storage_type(cls, v):
        allowed_types = {"TELEGRAM", "AWS_S3", "LOCAL"}
        if v.type.upper() not in allowed_types:
            raise ValueError(f'photo_storage.type must be one of {allowed_types}')
        return v


def load_config_from_yaml(file_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


# Load settings

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_PATH = os.path.join(SETTINGS_DIR, 'config.yaml')
config_path = os.getenv('CONFIG_PATH', DEFAULT_CONFIG_PATH)
# config_path = os.getenv('CONFIG_PATH', 'config.yaml')
config_data = load_config_from_yaml(config_path)
settings = Settings(**config_data)
