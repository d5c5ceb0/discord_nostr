class DiscordCollectorException(Exception):
    """基础异常类"""
    pass


class DatabaseError(DiscordCollectorException):
    """数据库相关错误"""
    pass


class DiscordAPIError(DiscordCollectorException):
    """Discord API相关错误"""
    pass


class NostrSyncError(DiscordCollectorException):
    """Nostr同步相关错误"""
    pass


class ValidationError(DiscordCollectorException):
    def __init__(self, *args: object):
        super().__init__(args)
        self.messages = None

    """数据验证错误"""
    pass
