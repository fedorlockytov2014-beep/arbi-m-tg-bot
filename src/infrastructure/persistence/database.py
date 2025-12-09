from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine


def create_engine(database_url: str) -> AsyncEngine:
    """
    Создает асинхронный движок базы данных.
    
    Args:
        database_url: URL подключения к базе данных
        
    Returns:
        AsyncEngine: Асинхронный движок SQLAlchemy
    """
    return create_async_engine(database_url)