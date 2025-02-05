from functools import wraps
from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError
from utils.logger import Logger

logger = Logger('error_handler')


class APIError(Exception):
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


def handle_exceptions(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({
                'error': 'Validation error',
                'message': str(e.messages)
            }), 400
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}")
            return jsonify({
                'error': 'Database error',
                'message': 'Error accessing database'
            }), 500
        except APIError as e:
            logger.error(f"API error: {str(e.message)}")
            return jsonify(e.to_dict()), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred'
            }), 500

    return decorated_function
