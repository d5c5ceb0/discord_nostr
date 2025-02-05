import os
from datetime import timedelta
import base64


class Config:
    # Discord配置
    DISCORD_TOKEN = 'MTMzMTU1NTA4OTA0Mjg5ODk1NQ.G4g9m8.BCdd0yuh0VEVQW6GyOFCOsscUwQoU9x-nBdbxM'
    
    # 数据库配置
    DB_HOST = 'localhost'
    DB_PORT = 3306
    DB_USER = 'root'
    DB_PASSWORD = '123456'
    DB_NAME = 'discord'
    
    # Nostr配置
    NOSTR_RELAY_URLS = ['ws://144.126.138.135:10548']
    NOSTR_PRIVATE_KEY = os.getenv('NOSTR_PRIVATE_KEY', 'nsec1ufnus6pju578ste3v90xd5m2decpuzpql2295m3sknqcjzyys9ls0qlc85')

    # API配置
    API_PORT = int(os.getenv('API_PORT', 8888))
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    API_KEY = os.getenv('API_KEY', 'your-api-key')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', base64.urlsafe_b64encode(os.urandom(32)))
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # 安全headers
    SECURITY_HEADERS = {
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'X-Content-Type-Options': 'nosniff',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
    }
    
    # Discord API 限制配置
    DISCORD_RATE_LIMIT = {
        'messages_per_second': 50,
        'bulk_delete_limit': 100,
    }