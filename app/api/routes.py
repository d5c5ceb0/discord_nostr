from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError
from app.models.database import get_db
from app.services.database_service import DatabaseService
from app.middleware.error_handler import handle_exceptions
from app.validators.schemas import (
    ChannelCreateSchema,
    ChannelUpdateSchema,
    ChannelDeleteSchema
)
from utils.exceptions import ValidationError
from utils.logger import Logger

api = Blueprint('api', __name__)
logger = Logger('api')

db_service = DatabaseService()


@api.route('/channels/<channel_id>/total', methods=['GET'])
@handle_exceptions
def get_channel_interactions(channel_id: int):
    """
    获取频道互动总数
    ---
    parameters:
      - name: channel_id
        in: path
        type: string
        required: true
        description: Discord频道ID
    responses:
      200:
        description: 成功返回频道统计数据
      404:
        description: 频道未找到
      500:
        description: 服务器错误
    """
    db = next(get_db())
    try:
        # 验证频道是否存在
        channel = DatabaseService.get_channel(db, channel_id)
        if not channel:
            return jsonify({
                'error': 'Channel not found',
                'channel_id': channel_id
            }), 404

        # 获取指定频道的消息总数
        total = DatabaseService.get_channel_interaction_count(db, channel_id)

        return jsonify({
            'channel_id': channel_id,
            'total_interactions': total
        })
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting channel interactions: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_channel_interactions: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/users/<user_id>/interactions', methods=['GET'])
@handle_exceptions
def get_user_interactions(user_id: str):
    """
    获取用户互动统计
    ---
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: Discord用户ID
      - start_time
        in: query
        type: long
        required: false
        description: 开始时间
      - end_time
        in: query
        type: long
        required: false
        description: 结束时间

    responses:
      200:
        description: 成功返回用户统计数据
      404:
        description: 用户未找到
      500:
        description: 服务器错误
    """
    start_time = request.args.get('start_time', default=None, type=int)
    end_time = request.args.get('end_time', default=None, type=int)
    db = next(get_db())
    try:
        total, per_channel = DatabaseService.get_user_interaction_stats(db, user_id, start_time, end_time)

        if total == 0:
            return jsonify({
                'error': 'No interactions found',
                'user_id': user_id
            }), 404

        return jsonify({
            'user_id': user_id,
            'total_interactions': total,
            'per_channel': per_channel
        })
    except SQLAlchemyError as e:
        logger.error(f"Database error when getting user interactions: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_user_interactions: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/users/<user_id>/interactions_history', methods=['GET'])
@handle_exceptions
def get_user_interactions_history(user_id: str):
    """
    获取用户互动历史
    ---
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: Discord用户ID
      - name: channel_id
        in: query
        type: string
        required: false
        description: 频道ID (可选)
      - name: offset
        in: query
        type: integer
        required: false
        description: 分页偏移量
      - name: limit
        in: query
        type: integer
        required: false
        description: 分页大小
    responses:
      200:
        description: 成功返回用户互动历史
      404:
        description: 未找到互动记录
      500:
        description: 服务器错误
    """
    channel_id = request.args.get('channel_id', default=None, type=str)
    offset = request.args.get('offset', default=0, type=int)
    limit = request.args.get('limit', default=10, type=int)

    db = next(get_db())
    try:
        message_count, messages = DatabaseService.get_user_interaction_history(
            db, user_id, channel_id, offset, limit
        )

        if message_count == 0:
            return jsonify({
                'error': 'No interactions found',
                'user_id': user_id
            }), 404

        return jsonify({
            'user_id': user_id,
            'message_count': message_count,
            'messages': messages
        })

    except SQLAlchemyError as e:
        logger.error(f"Database error when getting user interaction history: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_user_interactions_history: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/channels', methods=['POST'])
@handle_exceptions
def add_channel():
    """
    添加新频道
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ChannelCreate'
    responses:
      201:
        description: 频道创建成功
      400:
        description: 参数验证错误
      409:
        description: 频道已存在
      500:
        description: 服务器错误
    """
    db = next(get_db())
    try:
        # 验证请求数据
        schema = ChannelCreateSchema()
        validated_data = schema.load(request.json)

        # 添加频道
        channel_id = DatabaseService.add_channel(db, validated_data)

        return jsonify({
            'status': 'success',
            'message': 'Channel added successfully',
            'channel_id': channel_id
        }), 201

    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e.messages)
        }), 400
    except ValueError as e:
        return jsonify({
            'error': 'Channel already exists',
            'message': str(e)
        }), 409
    except SQLAlchemyError as e:
        logger.error(f"Database error when adding channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in add_channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/channels', methods=['PUT'])
@handle_exceptions
def update_channel():
    """
    更新频道信息
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ChannelUpdate'
    responses:
      200:
        description: 频道更新成功
      400:
        description: 参数验证错误
      404:
        description: 频道不存在
      500:
        description: 服务器错误
    """
    db = next(get_db())
    try:
        # 验证请求数据
        schema = ChannelUpdateSchema()
        validated_data = schema.load(request.json)

        # 更新频道
        success = DatabaseService.update_channel(db, validated_data)

        if not success:
            return jsonify({
                'error': 'Channel not found',
                'channel_id': validated_data['channel_id']
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Channel updated successfully'
        })

    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e.messages)
        }), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error when updating channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in update_channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/channels', methods=['DELETE'])
@handle_exceptions
def delete_channel():
    """
    删除频道
    ---
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ChannelDelete'
    responses:
      200:
        description: 频道删除成功
      400:
        description: 参数验证错误
      404:
        description: 频道不存在
      500:
        description: 服务器错误
    """
    db = next(get_db())
    try:
        # 验证请求数据
        schema = ChannelDeleteSchema()
        validated_data = schema.load(request.json)

        # 删除频道
        success = DatabaseService.delete_channel(db, validated_data)

        if not success:
            return jsonify({
                'error': 'Channel not found',
                'channel_id': validated_data['channel_id']
            }), 404

        return jsonify({
            'status': 'success',
            'message': 'Channel deleted successfully'
        })

    except ValidationError as e:
        return jsonify({
            'error': 'Validation error',
            'message': str(e.messages)
        }), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error when deleting channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in delete_channel: {str(e)}")
        db.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()


@api.route('/ping', methods=['GET'])
@handle_exceptions
def ping():
    """
    服务健康检查接口
    ---
    parameters:
      - name: service_id
        in: query
        type: string
        required: true
        description: 服务的唯一标识符
    responses:
      200:
        description: 服务在线
      404:
        description: 服务未找到
    """
    app = current_app
    if not app.name:
        return jsonify({
            'status': 'error',
            'message': 'Service not found'
        })

    return jsonify({
        'status': 'success',
        'message': 'service is online'
    })

@api.route('/users/interactions_history', methods=['GET'])
@handle_exceptions
def get_interactions_history():
    """
    获取用户互动历史
    ---
    parameters:
      - name: channel_id
        in: query
        type: string
        required: false
        description: 频道ID (可选)
      - name: offset
        in: query
        type: integer
        required: false
        description: 分页偏移量
      - name: limit
        in: query
        type: integer
        required: false
        description: 分页大小
      - start_time
        in: query
        type: long
        required: false
        description: 开始时间
      - end_time
        in: query
        type: long
        required: false
        description: 结束时间
    responses:
      200:
        description: 成功返回用户互动历史
      404:
        description: 未找到互动记录
      500:
        description: 服务器错误
    """
    channel_id = request.args.get('channel_id', default=None, type=str)
    offset = request.args.get('offset', default=0, type=int)
    limit = request.args.get('limit', default=10, type=int)
    start_time = request.args.get('start_time', default=None, type=int)
    end_time = request.args.get('end_time', default=None, type=int)

    db = next(get_db())
    try:
        message_count, messages = DatabaseService.get_interaction_history(
            db, channel_id, offset, limit, start_time, end_time
        )

        if message_count == 0:
            return jsonify({
                'error': 'No interactions found',
            }), 404

        return jsonify({
            'message_count': message_count,
            'messages': messages
        })

    except SQLAlchemyError as e:
        logger.error(f"Database error when getting user interaction history: {str(e)}")
        return jsonify({
            'error': 'Database error',
            'message': 'Error accessing database'
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_user_interactions_history: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    finally:
        db.close()
