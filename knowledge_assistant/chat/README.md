# Chat 模块

## 简介

Chat模块是知识助手系统的核心组件之一，提供智能对话和问答服务。该模块整合了RAG技术，能够基于知识库内容提供准确、相关的回答，支持会话上下文管理和历史记录保存。

## 目录结构

```
chat/
├── migrations/       # 数据库迁移文件
├── models/           # 模型文件目录
│   ├── __init__.py
│   ├── message_models.py  # 消息相关模型
│   └── session_models.py  # 会话相关模型
├── service/          # 服务层目录
│   ├── __init__.py
│   ├── rag_chat_service.py  # RAG聊天服务
│   └── vector_db_service.py  # 向量数据库服务
├── __init__.py       # 包初始化文件
├── admin.py          # Django管理后台配置
├── apps.py           # 应用程序配置
├── models.py         # 模型导入文件
├── serializers.py    # REST API序列化器
├── tests.py          # 测试代码
├── urls.py           # URL路由配置
└── views.py          # 视图处理函数
```

## 主要功能

- **聊天会话管理**：创建、查询、更新聊天会话
- **消息处理**：发送、接收、存储消息
- **RAG集成**：基于检索增强生成的智能回答
- **上下文管理**：保持会话上下文连贯性
- **历史记录**：保存和查询历史对话

## API端点

- `/api/chat/sessions/` - 管理聊天会话
- `/api/chat/sessions/{id}/` - 特定会话操作
- `/api/chat/sessions/{id}/messages/` - 管理会话消息
- `/api/chat/message/{id}/` - 特定消息操作

## 使用示例

### 创建新会话
```http
POST /api/chat/sessions/
Content-Type: application/json
Authorization: Token {user_token}

{
  "title": "关于Python的问答",
  "knowledge_base_id": 1
}
```

### 发送消息
```http
POST /api/chat/sessions/{session_id}/messages/
Content-Type: application/json
Authorization: Token {user_token}

{
  "content": "什么是Python装饰器?",
  "message_type": "user"
}
```

## 数据模型

### Session模型
表示一个完整的聊天会话，包含会话元数据和相关消息。

### Message模型
表示会话中的单条消息，包含内容、发送时间、发送者等信息。

## 服务组件

### RAG聊天服务
整合检索和生成功能，为用户问题提供基于知识库的精准回答。

### 向量数据库服务
处理文档嵌入向量的存储和检索，支持相似度搜索。

## 依赖项

- Django REST Framework
- 向量数据库（FAISS等）
- LLM模型接口
- 文本嵌入工具
