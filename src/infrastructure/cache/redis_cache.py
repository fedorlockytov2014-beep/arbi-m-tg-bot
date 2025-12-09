import json
import logging
from typing import Any, Optional, Union

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


class RedisCache:
    """
    Класс для работы с Redis кешом.
    """
    
    def __init__(self, redis_url: str):
        """
        Инициализирует Redis кеш.
        
        Args:
            redis_url: URL подключения к Redis
        """
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def connect(self):
        """Подключается к Redis."""
        self._client = redis.from_url(self.redis_url)
        try:
            # Проверяем подключение
            await self._client.ping()
            logger.info("Подключение к Redis установлено", redis_url=self.redis_url)
        except Exception as e:
            logger.error("Ошибка подключения к Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Отключается от Redis."""
        if self._client:
            await self._client.close()
            logger.info("Отключение от Redis выполнено")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Получает значение из кеша.
        
        Args:
            key: Ключ
            
        Returns:
            Значение или None если ключ не найден
        """
        if not self._client:
            logger.warning("Redis клиент не инициализирован")
            return None
        
        try:
            value = await self._client.get(key)
            if value is None:
                return None
            
            # Десериализуем JSON
            return json.loads(value)
        except Exception as e:
            logger.error("Ошибка при получении значения из кеша", key=key, error=str(e))
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Сохраняет значение в кеш.
        
        Args:
            key: Ключ
            value: Значение
            ttl: Время жизни в секундах
            
        Returns:
            bool: Успешность операции
        """
        if not self._client:
            logger.warning("Redis клиент не инициализирован")
            return False
        
        try:
            # Сериализуем в JSON
            serialized_value = json.dumps(value, ensure_ascii=False)
            
            # Сохраняем с TTL если указан
            if ttl:
                result = await self._client.setex(key, ttl, serialized_value)
            else:
                result = await self._client.set(key, serialized_value)
            
            logger.debug("Значение сохранено в кеш", key=key, ttl=ttl)
            return result
        except Exception as e:
            logger.error("Ошибка при сохранении значения в кеш", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Удаляет значение из кеша.
        
        Args:
            key: Ключ
            
        Returns:
            bool: Успешность операции
        """
        if not self._client:
            logger.warning("Redis клиент не инициализирован")
            return False
        
        try:
            result = await self._client.delete(key)
            logger.debug("Значение удалено из кеша", key=key)
            return bool(result)
        except Exception as e:
            logger.error("Ошибка при удалении значения из кеша", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Проверяет существование ключа в кеше.
        
        Args:
            key: Ключ
            
        Returns:
            bool: Существует ли ключ
        """
        if not self._client:
            logger.warning("Redis клиент не инициализирован")
            return False
        
        try:
            result = await self._client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Ошибка при проверке существования ключа", key=key, error=str(e))
            return False