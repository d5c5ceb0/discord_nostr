from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import json
from app.validators.schemas import BaseChannelSchema


class SwaggerDocs:
    def __init__(self):
        self.spec = APISpec(
            title="Discord Data Collector API",
            version="1.0.0",
            openapi_version="3.0.2",
            plugins=[MarshmallowPlugin()],
            info={
                "description": "API for collecting and managing Discord channel data",
                "contact": {"email": "your-email@example.com"}
            }
        )
        
        # 注册所有schemas
        self.register_schemas()
        # 注册所有路径
        self.register_paths()
        # self.spec.components.security_scheme(
        #     "ApiKeyAuth",
        #     {
        #         "type": "apiKey",
        #         "in": "header",
        #         "name": "X-API-Key"
        #     }
        # )
    
    def register_schemas(self):
        # 注册请求/响应模型
        self.spec.components.schema("Channel", schema=BaseChannelSchema)

    def register_paths(self):
        # 频道统计接口
        self.spec.path(
            path="/api/channels/{channel_id}/total",
            operations={
                "get": {
                    "tags": ["channels"],
                    "summary": "Get total interactions for a channel",
                    "parameters": [
                        {
                            "name": "channel_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful operation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "channel_id": {"type": "string"},
                                            "total_interactions": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "Channel not found"}
                    }
                }
            }
        )

        # 用户互动统计接口
        self.spec.path(
            path="/api/users/{user_id}/interactions",
            operations={
                "get": {
                    "tags": ["users"],
                    "summary": "Get user interaction statistics",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "start_time",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "long"}
                        },
                        {
                            "name": "end_time",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "long"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful operation",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "string"},
                                            "total_interactions": {"type": "integer"},
                                            "per_channel": {
                                                "channel_id": {"type": "string"},
                                                "count": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {"description": "User not found"}
                    }
                }
            }
        )

        # 用户互动历史接口
        self.spec.path(
            path="/api/users/{user_id}/interactions_history",
            operations={
                "get": {
                    "tags": ["users"],
                    "summary": "Get user interaction history",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "Discord用户ID"
                        },
                        {
                            "name": "channel_id",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"},
                            "description": "频道ID (可选), 如果没有channel_id, 则返回所有频道的互动历史"
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 0},
                            "description": "分页偏移量"
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 10},
                            "description": "分页大小"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "成功返回用户互动历史",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {
                                                "type": "string",
                                                "description": "用户ID"
                                            },
                                            "message_count": {
                                                "type": "integer",
                                                "description": "返回消息的数量"
                                            },
                                            "messages": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "channel_id": {
                                                            "type": "string",
                                                            "description": "频道ID"
                                                        },
                                                        "message": {
                                                            "type": "string",
                                                            "description": "消息内容"
                                                        },
                                                        "timestamp": {
                                                            "type": "string",
                                                            "description": "消息时间",
                                                            "example": "Sun, 26 Jan 2025 05:35:47 -0000"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "未找到互动记录"
                        },
                        "500": {
                            "description": "服务器错误"
                        }
                    }
                }
            }
        )

        # 频道管理接口
        self.spec.path(
            path="/api/channels",
            operations={
                "post": {
                    "tags": ["channels"],
                    "summary": "Add new channel",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Channel"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Channel added successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "message": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        )

    def get_swagger_spec(self):
        return json.dumps(self.spec.to_dict())