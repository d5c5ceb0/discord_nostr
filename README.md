### 1. API接口文档

#### 1.1 获取频道互动总数
```
GET /channels/{channel_id}/total

参数:
- channel_id: Discord频道ID (path参数)

返回:
{
  "channel_id": "频道ID",
  "total_interactions": 互动总数
}

状态码:
- 200: 成功
- 404: 频道未找到
```

#### 1.2 获取用户互动统计
```
GET /users/{user_id}/interactions

参数:
- user_id: Discord用户ID (path参数)

返回:
{
  "user_id": "用户ID",
  "total_interactions": 总互动数,
  "per_channel": [
    {
      "channel_id": "频道ID",
      "count": 该频道互动数
    }
  ]
}

状态码:
- 200: 成功
- 404: 用户未找到
```

#### 1.3 添加频道
```
POST /channels

请求体:
{
  "channel_id": "频道ID",
  "collect_start_time": "采集开始时间",
  "collect_end_time": "采集结束时间",
  "update_frequency": "更新频率",
  "expiration_time": "过期时间"
}

返回:
{
  "status": "success/failed",
  "message": "操作结果描述"
}
```

#### 1.4 更新频道
```
PUT /channels

请求体:
{
  "channel_id": "频道ID",
  "collect_start_time": "采集开始时间",
  "collect_end_time": "采集结束时间",
  "update_frequency": "更新频率",
  "expiration_time": "过期时间"
}

返回:
{
  "status": "success/failed",
  "message": "操作结果描述"
}
```

#### 1.5 删除频道
```
DELETE /channels

请求体:
{
  "channel_id": "频道ID"
}

返回:
{
  "status": "success/failed",
  "message": "操作结果描述"
}
```

### 2. 数据库设计文档

#### 2.1 discord_interaction 表
存储Discord互动消息数据
```sql
字段说明:
- interaction_id: 主键
- message_id: Discord消息ID
- channel_id: Discord频道ID
- user_id: 用户ID
- username: 用户名
- interaction_content: 发言内容
- interaction_time: 发言时间
- post_time: 帖子发布时间
- collect_time: 数据采集时间
- is_published: 是否已发布到Nostr

索引:
- PRIMARY KEY (interaction_id)
- UNIQUE KEY idx_unique_messageId (message_id)
- INDEX idx_channelId_userId (channel_id, user_id)
```

#### 2.2 discord_channel_collect_log 表
记录频道消息采集日志
```sql
字段说明:
- id: 主键
- channel_id: Discord频道ID
- collect_time: 采集时间
- collect_start_time: 采集开始时间
- collect_end_time: 采集结束时间
- collect_message_count: 采集消息数
- collect_status: 采集状态(1成功/0失败/2进行中)
- collect_error_message: 采集失败原因

索引:
- PRIMARY KEY (id)
- INDEX idx_channelId_collectTime (channel_id, collect_time)
```

#### 2.3 discord_channel 表
频道配置信息
```sql
字段说明:
- id: 主键
- channel_id: Discord频道ID
- collect_start_time: 采集开始时间
- collect_end_time: 采集结束时间
- update_frequency: 更新频率
- expiration_time: 过期时间
- create_at: 创建时间
- update_at: 更新时间

索引:
- PRIMARY KEY (id)
- INDEX idx_channelId (channel_id)
```

### 3. Nostr Relay同步说明

#### 3.1 配置说明
```python
NOSTR_RELAY_URLS = ['ws://xxx:port'] # Nostr中继节点地址
NOSTR_PRIVATE_KEY = 'nsec...'  # Nostr私钥
```

#### 3.2 同步事件格式
发言事件
```json
{
  "id": "事件唯一ID",
  "pubkey": "TEE节点公钥",
  "created_at": "同步时间戳",
  "kind": 1,
  "tags": [
    ["t", "discord"],
    ["channel_id", "Discord频道ID"],
    ["user_id", "用户Discord ID"],
    ["created_at", "发言时间戳"],
    ["message_id", "原消息ID"],
    ["username", "用户名"]
  ],
  "content": "发言内容",
  "sig": "事件签名"
}
```
点赞事件
```json
{
    "id": "<事件唯一ID>",
    "pubkey": "<TEE节点公钥>",
    "created_at": "<TEE节点同步时间戳>",
    "kind": 7,
    "tags": [
        ["t", "discord"],  // 标识事件来源于Discord
        ["channel_id", "<Discord频道ID>"],  // 反应所在的频道ID
        ["user_id", "<反应用户Discord ID>"],  // 反应用户的ID
        ["username", "<反应用户用户名>"],  // 反应用户的用户名
        ["created_at", "<点赞时间>"],
        ["message_id", "<被反应的消息ID>"],  // 被反应的消息ID
        ["e", "<被反应消息的Nostr事件ID>"],  // 被反应消息的Nostr事件ID
        ["reaction", "<反应类型，如👍>"]  // 反应的具体内容（如emoji）
    ],
    "content": "",
    "sig": "<事件签名>"
}
```
转发事件
```json
{
    "id": "<事件唯一ID>",
    "pubkey": "<TEE节点公钥>",
    "created_at": "<TEE节点同步时间戳>",
    "kind": 6,
    "tags": [
        ["t", "discord"],  // 标识事件来源于Discord
        ["channel_id", "<Discord频道ID>"],  // 转发所在的频道ID
        ["user_id", "<转发用户Discord ID>"],  // 转发用户的ID
        ["username", "<转发用户用户名>"],  // 转发用户的用户名
        ["created_at", "<转发时间>"],
        ["message_id", "<被转发消息ID>"],  // 被转发消息的ID
        ["e", "<被转发消息的事件ID>"]  // 被转发消息的Nostr事件ID
    ],
    "content": "",
    "sig": "<事件签名>"
}
```
