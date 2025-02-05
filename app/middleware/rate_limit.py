# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from config.config import Config
#
# limiter = Limiter(
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"],
#     storage_uri=Config.REDIS_URL
# )
#
#
# def configure_rate_limits(app):
#     limiter.init_app(app)
#
#     # 为特定端点配置限制
#     @limiter.limit("10 per minute")
#     @app.route("/api/channels/<channel_id>/total")
#     def get_channel_total(channel_id):
#         pass
#
#     @limiter.limit("10 per minute")
#     @app.route("/api/users/<user_id>/interactions")
#     def get_user_interactions(user_id):
#         pass
