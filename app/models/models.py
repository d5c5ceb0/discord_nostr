from enum import Enum

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, SmallInteger, Index
from sqlalchemy.sql import func
from app.models.database import Base


class Channel(Base):
    """频道表"""
    __tablename__ = "discord_channel"

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    channel_id = Column(BigInteger, nullable=False, index=True, comment='频道Id')
    collect_start_time = Column(DateTime, nullable=True, comment='采集开始时间')
    collect_end_time = Column(DateTime, nullable=True, comment='采集结束时间')
    update_frequency = Column(String(10), nullable=True,
                              comment='互动数据更新频率 (10m:十分钟, 1h:一小时, 2d:两天)')
    expiration_time = Column(String(10), nullable=True,
                             comment='互动数据过期时间 (如1w:一周,1m:一个月,1y:一年)')
    create_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    update_at = Column(DateTime, nullable=False, server_default=func.now(),
                       onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<Channel(id={self.id}, channel_id={self.channel_id})>"


class Interaction(Base):
    """发言消息表"""
    __tablename__ = "discord_interaction"

    interaction_id = Column(Integer, primary_key=True, autoincrement=True,
                            comment='primary key')
    message_id = Column(BigInteger, nullable=False, comment='消息Id')
    channel_id = Column(BigInteger, nullable=False, comment='频道Id')
    user_id = Column(BigInteger, nullable=False, comment='用户Id')
    username = Column(String(256), nullable=False, comment='用户名')
    interaction_content = Column(Text, nullable=False, comment='发言内容')
    interaction_time = Column(DateTime, nullable=False, comment='发言时间')
    post_time = Column(DateTime, nullable=False, comment='帖子发布时间')
    collect_time = Column(DateTime, nullable=False, server_default=func.now(),
                          comment='采集时间')
    note = Column(String(256), nullable=True, comment='备注')
    type = Column(SmallInteger, nullable=False,
                  comment='发言类型 (1:文字 | 2:点赞 ｜ 3:转发 | 4:回复)')
    is_published = Column(Boolean, nullable=False, default=False,
                          comment='是否已发布 (1:已发布 | 0:未发布)')
    nostr_event_id = Column(String(256), nullable=True, comment='Nostr事件ID', default='')

    __table_args__ = (
        # 复合索引
        Index('idx_channelId_userId', 'channel_id', 'user_id'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': '发言消息表'
        }
    )

    def __repr__(self):
        return f"<Interaction(id={self.interaction_id}, message_id={self.message_id})>"


class ChannelCollectLog(Base):
    """频道消息采集日志表"""
    __tablename__ = "discord_channel_collect_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    channel_id = Column(BigInteger, nullable=False, comment='频道Id')
    collect_time = Column(DateTime, nullable=False, server_default=func.now(),
                          comment='采集时间')
    collect_start_time = Column(DateTime, nullable=True,
                                comment='本次采集时间区间(开始)')
    collect_end_time = Column(DateTime, nullable=True,
                              comment='本次采集时间区间(结束)')
    collect_message_count = Column(Integer, nullable=False, default=0,
                                   comment='采集消息数')
    collect_status = Column(SmallInteger, nullable=False,
                            comment='采集是否成功 (1:成功 | 0:失败 | 2:采集进行中)')
    collect_error_message = Column(Text, nullable=True, comment='采集失败原因')

    __table_args__ = (
        # 复合索引
        Index('idx_channelId_collectTime', 'channel_id', 'collect_time', postgresql_ops={'collect_time': 'DESC'}),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
            'comment': '频道消息采集日志表'
        }
    )

    def __repr__(self):
        return f"<ChannelCollectLog(id={self.id}, channel_id={self.channel_id})>"


class InteractionType(Enum):
    """互动类型枚举"""
    MESSAGE = 1  # 文字消息
    LIKE = 2  # 点赞
    RETWEET = 3  # 转发
    REPLY = 4    # 回复


class CollectStatus(Enum):
    """采集状态枚举"""
    FAILED = 0  # 失败
    SUCCESS = 1  # 成功
    IN_PROGRESS = 2  # 进行中
