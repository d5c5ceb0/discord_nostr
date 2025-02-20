# Discord Nostr 项目部署指南

## 1. 克隆项目
```bash
git clone https://github.com/你的用户名/discord_nostr.git
cd discord_nostr
```

## 2. 安装 uv 包管理工具
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 3. 创建并激活虚拟环境
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

## 4. 安装项目依赖
```bash
# 使用 uv 安装依赖
uv pip install -r requirements.txt
```

## 5. 配置环境
编辑 `config/config.py` 文件，设置以下必要配置：

```python
# Discord配置
DISCORD_TOKEN = '你的Discord机器人Token'

# Nostr配置
NOSTR_RELAY_URLS = ['你的Nostr中继URL']
NOSTR_PRIVATE_KEY = '你的Nostr私钥'

# 数据库配置
DB_HOST = '数据库主机地址'
DB_PORT = 3306
DB_USER = '数据库用户名'
DB_PASSWORD = '数据库密码'
DB_NAME = 'discord'
```

## 6. 设置执行权限并运行
```bash
chmod +x restart.sh
sh restart.sh
```

## 7. 验证部署
检查 `logs/main.log` 确认服务是否正常运行：
```bash
tail -f logs/main.log
```

## 注意事项
- 确保已安装 Python 3.8 或更高版本
- 确保数据库服务已启动且可访问
- 请妥善保管各项密钥和token信息
