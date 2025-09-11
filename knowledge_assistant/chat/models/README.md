# Chat 模型目录

## 简介

此目录包含与聊天功能相关的数据模型定义，包括聊天会话和消息记录。模型分为会话模型和消息模型两个文件，以实现清晰的代码组织和关注点分离。

## 文件说明

### session_models.py

此文件定义了与聊天会话相关的模型类：

- **ChatSession**：表示用户的一个完整聊天会话，包含会话标题、创建时间、关联的知识库等信息
- **SessionTag**：会话标签，用于对会话进行分类和归档
- **SessionSettings**：会话特定设置，如模型参数、上下文窗口大小等

### message_models.py

此文件定义了与聊天消息相关的模型类：

- **Message**：表示会话中的单条消息，包含消息内容、发送时间、消息类型等
- **MessageAttachment**：消息附件，支持图片、文档等多媒体内容
- **RetrievalResult**：存储RAG检索结果，包括相关文档片段、相似度得分等

## 模型关系

- 一个`ChatSession`对应多个`Message`（一对多关系）
- 一个`ChatSession`对应多个`SessionTag`（多对多关系）
- 一个`ChatSession`对应一个`SessionSettings`（一对一关系）
- 一个`Message`可以关联多个`RetrievalResult`（一对多关系）

## 使用示例

```python
# 获取会话及其消息
session = ChatSession.objects.get(id=1)
messages = session.message_set.all().order_by('created_at')

# 创建新消息并关联检索结果
message = Message.objects.create(
    session=session,
    content="用户问题的回答",
    message_type="assistant"
)
RetrievalResult.objects.create(
    message=message,
    source_document="document1.pdf",
    content_snippet="相关文档片段",
    relevance_score=0.92
)
```

## 数据迁移

当修改模型后，需要创建和应用迁移：

```bash
python manage.py makemigrations chat
python manage.py migrate chat
```
