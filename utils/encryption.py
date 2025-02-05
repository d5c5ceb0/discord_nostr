from cryptography.fernet import Fernet
from config.config import Config


class Encryptor:
    def __init__(self):
        # 确保加密密钥存在且格式正确
        if not Config.ENCRYPTION_KEY:
            # 如果没有设置密钥，生成一个新的
            self.key = Fernet.generate_key()
        else:
            # 如果密钥是字符串，需要编码为 bytes
            self.key = Config.ENCRYPTION_KEY.encode() if isinstance(Config.ENCRYPTION_KEY, str) else Config.ENCRYPTION_KEY
            
        self.cipher_suite = Fernet(self.key)
    
    def encrypt(self, data):
        if data is None:
            return None
        # 确保数据是字符串类型
        data_str = str(data)
        return self.cipher_suite.encrypt(data_str.encode())
    
    def decrypt(self, encrypted_data):
        if encrypted_data is None:
            return None
        # 解密数据
        decrypted = self.cipher_suite.decrypt(encrypted_data)
        return decrypted.decode()