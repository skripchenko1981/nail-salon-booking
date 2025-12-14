import os
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import uuid
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Завантажити .env
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Конфігурація S3
S3_ENDPOINT = os.environ.get('S3_ENDPOINT')
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_REGION = os.environ.get('S3_REGION', 'hel1')

# Ініціалізація S3 клієнта
s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
    config=Config(signature_version='s3v4')
)

def upload_file_to_s3(file_content: bytes, file_extension: str) -> str:
    """
    Завантажити файл на S3 і повернути ключ файлу
    
    Args:
        file_content: Вміст файлу в байтах
        file_extension: Розширення файлу (наприклад: 'jpg', 'png')
    
    Returns:
        Ключ файлу в S3
    """
    # Генерація унікального імені файлу
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_id = uuid.uuid4().hex[:8]
    file_key = f"gallery-{timestamp}-{random_id}.{file_extension}"
    
    try:
        # Завантаження файлу
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=file_content,
            ContentType=f'image/{file_extension}'
        )
        return file_key
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        raise Exception(f"Failed to upload file: {str(e)}")

def generate_presigned_url(file_key: str, expiration: int = 3600) -> str:
    """
    Генерувати presigned URL для приватного файлу
    
    Args:
        file_key: Ключ файлу в S3
        expiration: Час дії URL в секундах (за замовчуванням 1 година)
    
    Returns:
        Presigned URL
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': file_key
            },
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        raise Exception(f"Failed to generate URL: {str(e)}")

def delete_file_from_s3(file_key: str) -> bool:
    """
    Видалити файл з S3
    
    Args:
        file_key: Ключ файлу в S3
    
    Returns:
        True якщо успішно видалено
    """
    try:
        s3_client.delete_object(
            Bucket=S3_BUCKET,
            Key=file_key
        )
        return True
    except ClientError as e:
        print(f"Error deleting file from S3: {e}")
        return False
