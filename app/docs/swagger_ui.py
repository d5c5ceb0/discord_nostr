from flask import Blueprint
from flask_swagger_ui import get_swaggerui_blueprint

from app.docs.swagger_config import SwaggerDocs

# Swagger UI的URL配置
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'


def create_swagger_blueprint():
    # 创建用于提供swagger.json的蓝图
    swagger_api = Blueprint('swagger_api', __name__)
    swagger_docs = SwaggerDocs()

    @swagger_api.route('/api/swagger.json')
    def create_swagger_spec():
        return swagger_docs.get_swagger_spec()

    # 创建Swagger UI蓝图
    swagger_ui = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Discord Data Collector API",
            'deepLinking': True,
            'displayOperationId': False,
            'displayRequestDuration': True,
            'docExpansion': 'list',
            'showExtensions': True,
            'showCommonExtensions': True,
            'supportedSubmitMethods': ['get', 'post', 'put', 'delete']
        }
    )

    return swagger_api, swagger_ui