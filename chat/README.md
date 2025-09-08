# 💬 聊天模块 (Chat)

<div align="center">
  <p><strong>知识助手项目的实时聊天与交流子系统</strong></p>
</div>

## 📋 模块简介

聊天模块为知识助手项目提供实时通信能力，支持用户间的消息交流、知识问答以及智能回复功能。通过集成RAG技术，聊天系统能够基于知识库内容提供精准的回答和建议。

## 🔑 核心功能

- **📨 消息管理**
  - 实时消息发送与接收
  - 聊天历史记录存储
  - 消息搜索与过滤
  - 未读消息通知

- **👥 对话管理**
  - 一对一私人对话
  - 群组聊天支持
  - 智能助手对话
  - 对话上下文维护

- **🤖 智能回复**
  - RAG技术增强的智能回复
  - 基于知识库的问题解答
  - 自然语言理解与生成
  - 上下文感知的回答

## 📁 目录结构

```
chat/
│
├── models/              # 模型定义
│   ├── __init__.py      # 模型初始化
│   ├── message_models.py # 消息模型
│   └── conversation_models.py # 对话模型
│
├── migrations/          # 数据库迁移文件
├── __init__.py         # 包初始化
├── admin.py            # 管理员配置
├── apps.py             # 应用配置
├── serializers.py      # 序列化器定义
├── urls.py             # URL路由配置
├── views.py            # 视图与API实现
└── tests.py            # 单元测试
```

## 🔌 API 接口

| 接口路径 | 方法 | 描述 | 权限 |
|---------|------|------|------|
| `/api/chat/conversations/` | GET | 获取对话列表 | 需认证 |
| `/api/chat/conversations/` | POST | 创建新对话 | 需认证 |
| `/api/chat/conversations/{id}/` | GET | 获取特定对话 | 需认证 |
| `/api/chat/messages/` | GET | 获取消息列表 | 需认证 |
| `/api/chat/messages/` | POST | 发送新消息 | 需认证 |
| `/api/chat/askbot/` | POST | 向智能助手提问 | 需认证 |

## 📊 数据模型

### 对话模型 (Conversation)
- `title`: 对话标题
- `participants`: 参与者（多对多关系）
- `created_at`: 创建时间
- `updated_at`: 最后更新时间
- `is_group`: 是否为群聊

### 消息模型 (Message)
- `conversation`: 所属对话（外键）
- `sender`: 发送者（外键）
- `content`: 消息内容
- `timestamp`: 发送时间
- `is_read`: 是否已读
- `attachment`: 附件（可选）

## 🧪 测试覆盖

- 消息发送与接收测试
- 对话创建与管理测试
- 智能回复功能测试
- WebSocket连接测试
- 并发和性能测试

## 🔗 与其他模块的关联

- 与**账户模块**集成，确认用户身份和权限
- 与**知识模块**集成，获取问题的回答内容
- 与**RAG技术**集成，实现智能对话与知识检索
