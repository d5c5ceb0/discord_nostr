import re


class DataCleaner:
    @staticmethod
    def clean_message_content(content: str) -> str:
        # 删除敏感信息
        content = re.sub(r'(https?://\S+)', '[URL]', content)
        content = re.sub(r'[\u0000-\u001F\u007F-\u009F]', '', content)
        return content.strip()
    
    @staticmethod
    def validate_channel_config(config: dict) -> bool:
        required_fields = ['channel_id', 'update_frequency', 'expiration_time']
        return all(field in config for field in required_fields)