import discord
from app import create_app
from config.config import Config
from utils.logger import Logger
from app.services.discord_collector import DiscordCollector

logger = Logger('main')


def run_discord_collector():
    """运行 Discord 收集器"""
    try:
        # 设置必要的意图
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True  # 添加服务器权限
        intents.guild_messages = True  # 添加消息权限

        # 创建并运行收集器
        collector = DiscordCollector(intents=intents)
        collector.run(Config.DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start Discord collector: {str(e)}")
        raise e


def run_flask_app():
    """运行 Flask 应用"""
    try:
        app = create_app(Config)
        app.run(host='0.0.0.0', port=Config.API_PORT)
    except Exception as e:
        logger.error(f"Failed to start Flask app: {str(e)}")
        raise e


if __name__ == '__main__':
    # 使用多进程运行 Discord 收集器和 Flask 应用
    from multiprocessing import Process

    # 创建进程
    discord_process = Process(target=run_discord_collector)
    flask_process = Process(target=run_flask_app)

    try:
        # 启动 Discord 进程
        logger.info("Starting Discord collector process...")
        discord_process.start()

        # 启动 Flask 进程
        logger.info("Starting Flask application process...")
        flask_process.start()

        # 等待进程结束
        discord_process.join()
        flask_process.join()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        # 优雅地关闭进程
        discord_process.terminate()
        flask_process.terminate()
        discord_process.join()
        flask_process.join()
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        # 确保进程被清理
        discord_process.terminate()
        flask_process.terminate()
        discord_process.join()
        flask_process.join()
        raise e