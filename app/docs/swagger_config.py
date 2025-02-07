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