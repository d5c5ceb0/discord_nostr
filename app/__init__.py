from flask import Flask
from app.api.routes import api
from app.docs.swagger_ui import create_swagger_blueprint
from config.config import Config
from flask_cors import CORS


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)  # 添加CORS支持

    # 注册API蓝图
    app.register_blueprint(api, url_prefix='/api')

    # 注册Swagger蓝图
    swagger_api, swagger_ui = create_swagger_blueprint()
    app.register_blueprint(swagger_api)
    app.register_blueprint(swagger_ui)

    # 配置速率限制
    # configure_rate_limits(app)

    # 添加安全headers
    @app.after_request
    def add_security_headers(response):
        for header, value in Config.SECURITY_HEADERS.items():
            response.headers[header] = value
        return response

    return app
