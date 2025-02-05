from marshmallow import Schema, fields, validates, validates_schema, ValidationError, EXCLUDE
import re


class BaseChannelSchema(Schema):
    """基础频道 Schema,定义所有可能的字段"""
    channel_id = fields.Str()
    start_time = fields.DateTime()
    end_time = fields.DateTime()
    update_frequency = fields.Str()
    expiration_time = fields.Str()

    class Meta:
        unknown = EXCLUDE  # 忽略未定义的字段

    def validate_update_frequency(self, value, field_name):
        """验证时间格式是否符合 数字+单位(s/m/h/d) 的格式"""
        pattern = r'^\d+[mhd]$'
        if not re.match(pattern, value):
            raise ValidationError(f"{field_name} must be a number followed by m/h/d (e.g., 30m, 24h, 7d)")

    def validate_expiration_time(self, value, field_name):
        """验证时间格式是否符合 数字+单位(s/m/h/d) 的格式"""
        pattern = r'^\d+[dmy]$'
        if not re.match(pattern, value):
            raise ValidationError(f"{field_name} must be a number followed by d/m/y (e.g., 30d, 1m, 2y)")


class ChannelCreateSchema(BaseChannelSchema):
    """创建频道时的 Schema
    - start_time, end_time 可选
    - 其他字段必填
    """
    channel_id = fields.Int(required=True, error_messages={"required": "channel_id is required"})
    update_frequency = fields.Str(required=True, error_messages={"required": "update_frequency is required"})
    expiration_time = fields.Str(required=True, error_messages={"required": "expiration_time is required"})

    @validates("update_frequency")
    def validate_update_frequency(self, value):
        """验证更新频率格式"""
        super().validate_update_frequency(value, "update_frequency")

    @validates("expiration_time")
    def validate_expiration_time(self, value):
        """验证过期时间格式"""
        super().validate_expiration_time(value, "expiration_time")

    @validates_schema
    def validate_times(self, data, **kwargs):
        """验证时间字段的合法性"""
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] > data['end_time']:
                raise ValidationError('start_time must be earlier than end_time')


class ChannelUpdateSchema(BaseChannelSchema):
    """更新频道时的 Schema
    - 仅 channel_id 必填
    - update_frequency 和 expiration_time 如果提供则需符合格式要求
    - 其他字段可选
    """
    channel_id = fields.Str(required=True, error_messages={"required": "channel_id is required"})
    update_frequency = fields.Str(required=False)
    expiration_time = fields.Str(required=False)

    @validates("update_frequency")
    def validate_update_frequency(self, value):
        """Validate update frequency format"""
        super().validate_update_frequency(value, "update_frequency")

    @validates("expiration_time")
    def validate_expiration_time(self, value):
        """Validate expiration time format"""
        super().validate_expiration_time(value, "expiration_time")

    @validates_schema
    def validate_times(self, data, **kwargs):
        """验证时间字段的合法性"""
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] > data['end_time']:
                raise ValidationError('start_time must be earlier than end_time')


class ChannelDeleteSchema(BaseChannelSchema):
    """删除频道时的 Schema
    - 仅 channel_id 必填
    """
    channel_id = fields.Str(required=True, error_messages={"required": "channel_id is required"})


class InteractionSchema(Schema):
    channel_id = fields.Str(required=True)
    user_id = fields.Str(required=True)
    username = fields.Str(required=True)
    interaction_content = fields.Str(required=True)
    interaction_time = fields.DateTime(required=True)
