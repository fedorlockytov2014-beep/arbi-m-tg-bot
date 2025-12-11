from typing import Union
from pydantic import BaseModel, Field, field_validator


class WarehouseId(BaseModel):
    """
    Value object для идентификатора склада.
    
    Attributes:
        value: Значение идентификатора склада
    """
    value: str = Field(..., min_length=1, max_length=36)
    
    @field_validator('value')
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """
        Валидирует формат UUID.
        
        Args:
            v: Значение идентификатора
            
        Returns:
            str: Валидированное значение
        """
        # Проверяем, является ли значение валидным UUID
        try:
            str(v)
        except ValueError:
            raise ValueError(f'Invalid str format: {v}')
        return v
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, WarehouseId):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)
