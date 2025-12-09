from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TodayStatisticsDTO(BaseModel):
    """
    DTO для получения статистики за сегодня.
    
    Attributes:
        warehouse_uid: UID склада
        chat_id: ID Telegram-чата
    """
    warehouse_uid: str
    chat_id: int


class WeeklyStatisticsDTO(BaseModel):
    """
    DTO для получения статистики за неделю.
    
    Attributes:
        warehouse_uid: UID склада
        chat_id: ID Telegram-чата
        week_start: Начало недели (опционально, по умолчанию текущая неделя)
    """
    warehouse_uid: str
    chat_id: int
    week_start: Optional[datetime] = None


class MonthlyStatisticsDTO(BaseModel):
    """
    DTO для получения статистики за месяц.
    
    Attributes:
        warehouse_uid: UID склада
        chat_id: ID Telegram-чата
        month: Месяц (опционально, по умолчанию текущий месяц)
    """
    warehouse_uid: str
    chat_id: int
    month: Optional[datetime] = None


class StatisticsByDateRangeDTO(BaseModel):
    """
    DTO для получения статистики за произвольный период.
    
    Attributes:
        warehouse_uid: UID склада
        chat_id: ID Telegram-чата
        date_from: Начало периода
        date_to: Конец периода
    """
    warehouse_uid: str
    chat_id: int
    date_from: datetime
    date_to: datetime