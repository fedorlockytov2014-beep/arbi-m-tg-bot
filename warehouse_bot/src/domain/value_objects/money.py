from decimal import Decimal
from typing import Union
from pydantic import BaseModel, Field, field_validator


class Money(BaseModel):
    """
    Value object для денежной суммы.
    
    Attributes:
        amount: Сумма в минимальных единицах (копейках/центах)
    """
    amount: int = Field(..., ge=0)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """
        Валидирует денежную сумму.
        
        Args:
            v: Сумма в минимальных единицах
            
        Returns:
            int: Валидированная сумма
        """
        if v < 0:
            raise ValueError('Сумма должна быть неотрицательной')
        return v

    @property
    def decimal_amount(self) -> Decimal:
        """
        Возвращает сумму в виде Decimal (рубли.копейки).
        
        Returns:
            Decimal: Сумма в виде Decimal
        """
        return Decimal(self.amount) / 100

    @property
    def formatted_amount(self) -> str:
        """
        Возвращает отформатированную строку суммы.
        
        Returns:
            str: Отформатированная строка (например, "123.45 RUB")
        """
        return f"{self.decimal_amount:.2f} RUB"

    def __str__(self) -> str:
        return self.formatted_amount

    def __add__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            return NotImplemented
        return Money(amount=self.amount + other.amount)

    def __sub__(self, other: 'Money') -> 'Money':
        if not isinstance(other, Money):
            return NotImplemented
        if self.amount < other.amount:
            raise ValueError('Результат вычитания не может быть отрицательным')
        return Money(amount=self.amount - other.amount)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount

    def __lt__(self, other) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount < other.amount

    def __le__(self, other) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount <= other.amount

    def __gt__(self, other) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount > other.amount

    def __ge__(self, other) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount >= other.amount

    @classmethod
    def from_decimal(cls, decimal_value: Union[Decimal, float, str, int]) -> 'Money':
        """
        Создаёт объект Money из Decimal/float/string/int.
        
        Args:
            decimal_value: Значение для конвертации
            
        Returns:
            Money: Новый объект Money
        """
        decimal_amount = Decimal(decimal_value)
        amount_in_minor_units = int(decimal_amount * 100)
        return cls(amount=amount_in_minor_units)

    @classmethod
    def from_rubles_kopecks(cls, rubles: int, kopecks: int = 0) -> 'Money':
        """
        Создаёт объект Money из рублей и копеек.
        
        Args:
            rubles: Количество рублей
            kopecks: Количество копеек (по умолчанию 0)
            
        Returns:
            Money: Новый объект Money
        """
        total_kopecks = rubles * 100 + kopecks
        return cls(amount=total_kopecks)