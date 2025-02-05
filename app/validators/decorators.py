from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError
from typing import Type, Any
from app.validators.schemas import BaseChannelSchema


def validate_schema(schema_class: Type[BaseChannelSchema]):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                schema = schema_class()
                validated_data = schema.load(request.json)
                return f(*args, validated_data=validated_data, **kwargs)
            except ValidationError as err:
                return jsonify({
                    'error': 'Validation error',
                    'message': err.messages
                }), 400

        return decorated_function

    return decorator
