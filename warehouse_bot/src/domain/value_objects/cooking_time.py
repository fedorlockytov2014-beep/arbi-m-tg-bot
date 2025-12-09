from typing import Union
from pydantic import BaseModel, Field, field_validator

from ...config.settings import settings


class CookingTime(BaseModel):
    """
    Value object для времени приготовления.
    
    Attributes:
        minutes: Время приготовления в минутах
    """
    minutes: int = Field(..., gt=0, le=settings.security.max_cooking_time_minutes)

    @field_validator('minutes')
    @classmethod
    def validate_minutes(cls, v: int) -> int:
        """
        Валидирует время приготовления.
        
        Args:
            v: Время в минутах
            
        Returns:
            int: Валидированное время в минутах
            
        Raises:
            ValueError: Если время выходит за допустимые пределы
        """
        if v <= 0:
            raise ValueError('Время приготовления должно быть положительным')
        if v > settings.security.max_cooking_time_minutes:
            raise ValueError(f'Время приготовления не может превышать {settings.security.max_cooking_time_minutes} минут')
        return v

    def __str__(self) -> str:
        return f"{self.minutes} мин"

    def __eq__(self, other) -> bool:
        if not isinstance(other, CookingTime):
            return False
        return self.minutes == other.minutes

    def __lt__(self, other) -> bool:
        if not isinstance(other, CookingTime):
            return NotImplemented
        return self.minutes < other.minutes

    def __le__(self, other) -> bool:
        if not isinstance(other, CookingTime):
            return NotImplemented
        return self.minutes <= other.minutes

    def __gt__(self, other) -> bool:
        if not isinstance(other, CookingTime):
            return NotImplemented
        return self.minutes > other.minutes

    def __ge__(self, other) -> bool:
        if not isinstance(other, CookingTime):
            return NotImplemented
        return self.minutes >= other.minutes

    @classmethod
    def from_minutes(cls, minutes: Union[int, float]) -> 'CookingTime':
        """
        Создаёт объект CookingTime из количества минут.
        
        Args:
            minutes: Время в минутах
            
        Returns:
            CookingTime: Новый объект CookingTime
        """
        return cls(minutes=int(minutes))