import discord
import requests
import socket
from app import create_app
from config.config import Config
from utils.logger import Logger
from app.services.discord_collector import DiscordCollector

logger = Logger('main')

def get_local_ip():
    """通过创建socket连接获取本机IP"""
    try:
        # 创建一个UDP socket连接
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 连接一个外部地址（不需要真实连接）
        s.connect(('8.8.8.8', 80))
        # 获取本地IP
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        logger.error(f"Error getting local IP: {str(e)}")
        return '127.0.0.1'


def register_service(host: str):
    """注册服务到心跳检测系统"""
    try:
        data = {
            'ip_or_domain': f"http://{host}:{Config.API_PORT}",
            'service_id': Config.SERVICE_ID
        }
        response = requests.post(
            f"{Config.HEARTBEAT_SERVICE_URL}/register-heartbeat",
            json=data,
            timeout=5
        )
        if response.status_code == 200:
            logger.info("Successfully registered service for heartbeat detection")
        else:
            logger.error(f"Failed to register service: {response.text}")
    except Exception as e:
        logger.error(f"Error registering service: {str(e)}")


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
        host = get_local_ip()  # 获取本机IP
        # 注册服务时使用实际IP
        register_service(host)
        # 启动应用
        app.run(host='0.0.0.0', port=Config.API_PORT)  # 仍然监听所有接口
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
        # discord_process.start()

        # 启动 Flask 进程
        logger.info("Starting Flask application process...")
        flask_process.start()

        # 等待进程结束
        #discord_process.join()
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