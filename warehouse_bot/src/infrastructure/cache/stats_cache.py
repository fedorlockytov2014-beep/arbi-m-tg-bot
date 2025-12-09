import json
import logging
from typing import Any, Dict, Optional, Union

import redis.asyncio as redis
from pydantic import BaseModel

from ...config.settings import settings

logger = logging.getLogger(__name__)

class StatsCache:
    """
    Сервис кеширования статистики.
    
    Attributes:
        redis_client: Асинхронный клиент Redis
    """
    
    def __init__(self, redis_url: str = settings.cache.redis_url):
        """
        Инициализирует кеш статистики.
        
        Args:
            redis_url: URL подключения к Redis
        """
        self.redis_client = redis.from_url(redis_url)
        
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получает значение из кеша.
        
        Args:
            key: Ключ кеша
            
        Returns:
            Optional[Dict[str, Any]]: Значение из кеша или None если не найдено
        """
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
            
            # Декодируем JSON
            return json.loads(value)
            
        except Exception as e:
            logger.error(
                "Ошибка при получении значения из кеша",
                extra={
                    "key": key,
                    "error": str(e),
                    "exc_info": True
                }
            )
            return None
        
    async def set(self, key: str, value: Union[Dict[str, Any], BaseModel], ttl: int) -> bool:
        """
        Сохраняет значение в кеш.
        
        Args:
            key: Ключ кеша
            value: Значение для сохранения
            ttl: Время жизни в секундах
            
        Returns:
            bool: True если сохранение прошло успешно
        """
        try:
            # Если передан BaseModel, конвертируем в dict
            if isinstance(value, BaseModel):
                value = value.model_dump()
            
            # Кодируем в JSON
            json_value = json.dumps(value, default=str)
            
            # Сохраняем в Redis с TTL
            result = await self.redis_client.setex(key, ttl, json_value)
            
            if result:
                logger.debug(
                    "Значение сохранено в кеш",
                    extra={
                        "key": key,
                        "ttl": ttl
                    }
                )
            
            return bool(result)
            
        except Exception as e:
            logger.error(
                "Ошибка при сохранении значения в кеш",
                extra={
                    "key": key,
                    "error": str(e),
                    "exc_info": True
                }
            )
            return False
        
    async def delete(self, key: str) -> bool:
        """
        Удаляет значение из кеша.
        
        Args:
            key: Ключ кеша
            
        Returns:
            bool: True если удаление прошло успешно
        """
        try:
            result = await self.redis_client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error(
                "Ошибка при удалении значения из кеша",
                extra={
                    "key": key,
                    "error": str(e),
                    "exc_info": True
                }
            )
            return False
        
    async def exists(self, key: str) -> bool:
        """
        Проверяет существование ключа в кеше.
        
        Args:
            key: Ключ кеша
            
        Returns:
            bool: True если ключ существует
        """
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(
                "Ошибка при проверке существования ключа в кеше",
                extra={
                    "key": key,
                    "error": str(e),
                    "exc_info": True
                }
            )
            return False