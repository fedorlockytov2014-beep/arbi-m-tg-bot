import uuid
from typing import List, Optional
import aioboto3
from botocore.exceptions import ClientError

from warehouse_bot.config.settings import settings
from .storage_interface import IStorageAdapter


class S3StorageAdapter(IStorageAdapter):
    """
    Адаптер для хранения файлов в AWS S3.
    
    Реализует интерфейс IStorageAdapter для работы с AWS S3.
    """

    def __init__(
        self,
        bucket_name: str = settings.photo_storage.s3.bucket_name,
        region: str = settings.photo_storage.s3.region,
        access_key: str = settings.photo_storage.s3.access_key,
        secret_key: str = settings.photo_storage.s3.secret_key,
        endpoint_url: Optional[str] = settings.photo_storage.s3.endpoint_url
    ):
        """
        Инициализирует S3 адаптер.
        
        Args:
            bucket_name: Имя бакета S3
            region: Регион S3
            access_key: Ключ доступа
            secret_key: Секретный ключ
            endpoint_url: URL эндпоинта (для совместимости с другими S3-совместимыми хранилищами)
        """
        self.bucket_name = bucket_name
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        
        # Конфигурация сессии
        self.session = aioboto3.Session()

    def _generate_filename(self, original_filename: str) -> str:
        """
        Генерирует случайное имя файла из 32 символов с сохранением расширения.
        
        Args:
            original_filename: Оригинальное имя файла
            
        Returns:
            str: Новое случайное имя файла
        """
        # Извлекаем расширение
        if '.' in original_filename:
            extension = original_filename.split('.')[-1]
            return f"{uuid.uuid4().hex}.{extension}"
        else:
            # Если расширение отсутствует, используем только UUID
            return f"{uuid.uuid4().hex}"

    async def upload_file(self, file_data: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Загружает файл в S3.
        
        Args:
            file_data: Байтовые данные файла
            filename: Оригинальное имя файла
            content_type: MIME-тип файла (опционально)
            
        Returns:
            str: URL загруженного файла
        """
        # Генерируем новое имя файла
        new_filename = self._generate_filename(filename)
        
        # Определяем content_type если не задан
        if content_type is None:
            if new_filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif new_filename.lower().endswith('.png'):
                content_type = 'image/png'
            elif new_filename.lower().endswith('.gif'):
                content_type = 'image/gif'
            else:
                content_type = 'application/octet-stream'
        
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url
            ) as s3_client:
                await s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=new_filename,
                    Body=file_data,
                    ContentType=content_type
                )
                
                # Формируем URL файла
                if self.endpoint_url:
                    # Для кастомного эндпоинта
                    file_url = f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{new_filename}"
                else:
                    # Для AWS S3
                    file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{new_filename}"
                
                return file_url
                
        except ClientError as e:
            raise Exception(f"Ошибка при загрузке файла в S3: {str(e)}")

    async def upload_files(self, files_data: List[bytes], filenames: List[str], content_types: Optional[List[str]] = None) -> List[str]:
        """
        Загружает несколько файлов в S3.
        
        Args:
            files_data: Список байтовых данных файлов
            filenames: Список оригинальных имен файлов
            content_types: Список MIME-типов файлов (опционально)
            
        Returns:
            List[str]: Список URL загруженных файлов
        """
        if content_types is None:
            content_types = [None] * len(files_data)
        
        urls = []
        for i, (file_data, filename, content_type) in enumerate(zip(files_data, filenames, content_types)):
            url = await self.upload_file(file_data, filename, content_type)
            urls.append(url)
        
        return urls

    async def get_file_url(self, file_key: str) -> str:
        """
        Получает URL файла по ключу.
        
        Args:
            file_key: Ключ файла в S3
            
        Returns:
            str: URL файла
        """
        if self.endpoint_url:
            # Для кастомного эндпоинта
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket_name}/{file_key}"
        else:
            # Для AWS S3
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_key}"

    async def delete_file(self, file_key: str) -> bool:
        """
        Удаляет файл из S3.
        
        Args:
            file_key: Ключ файла в S3
            
        Returns:
            bool: True если файл успешно удален, иначе False
        """
        try:
            async with self.session.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url
            ) as s3_client:
                await s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                
            return True
            
        except ClientError as e:
            raise Exception(f"Ошибка при удалении файла из S3: {str(e)}")