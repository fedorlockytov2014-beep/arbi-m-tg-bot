from abc import ABC, abstractmethod
from typing import List, Optional


class IStorageAdapter(ABC):
    """
    Абстрактный интерфейс для адаптера хранения файлов.
    
    Определяет контракт для всех операций хранения файлов:
    - Загрузка файлов
    - Получение URL файлов
    - Удаление файлов
    """

    @abstractmethod
    async def upload_file(self, file_data: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Загружает файл в хранилище.
        
        Args:
            file_data: Байтовые данные файла
            filename: Оригинальное имя файла
            content_type: MIME-тип файла (опционально)
            
        Returns:
            str: URL загруженного файла
        """
        pass

    @abstractmethod
    async def upload_files(self, files_data: List[bytes], filenames: List[str], content_types: Optional[List[str]] = None) -> List[str]:
        """
        Загружает несколько файлов в хранилище.
        
        Args:
            files_data: Список байтовых данных файлов
            filenames: Список оригинальных имен файлов
            content_types: Список MIME-типов файлов (опционально)
            
        Returns:
            List[str]: Список URL загруженных файлов
        """
        pass

    @abstractmethod
    async def get_file_url(self, file_key: str) -> str:
        """
        Получает URL файла по ключу.
        
        Args:
            file_key: Ключ файла в хранилище
            
        Returns:
            str: URL файла
        """
        pass

    @abstractmethod
    async def delete_file(self, file_key: str) -> bool:
        """
        Удаляет файл из хранилища.
        
        Args:
            file_key: Ключ файла в хранилище
            
        Returns:
            bool: True если файл успешно удален, иначе False
        """
        pass