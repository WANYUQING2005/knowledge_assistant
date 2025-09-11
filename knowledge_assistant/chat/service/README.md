# Chat 服务目录

## 简介

此目录包含chat模块的核心服务组件，负责处理RAG（检索增强生成）聊天功能和向量数据库操作。这些服务组件封装了复杂的业务逻辑，为视图层提供简洁的接口。

## 文件说明

### rag_chat_service.py

此文件提供RAG聊天服务的核心实现：

- 处理用户输入的问题
- 从向量数据库中检索相关文档片段
- 将检索结果与问题一起传递给大语言模型
- 生成基于检索内容的回答
- 管理对话上下文和历史记录

### vector_db_service.py

此文件负责与向量数据库的交互：

- 向量的存储和检索
- 相似度搜索功能
- 向量索引管理
- 向量数据库连接池管理

## 主要功能

- **智能问答**：基于RAG技术的智能问答服务
- **上下文管理**：保持对话的上下文连贯性
- **向量检索**：高效的向量相似度搜索
- **响应生成**：基于检索内容生成准确回答

## 使用示例

```python
# 使用RAG聊天服务
from chat.service.rag_chat_service import RAGChatService

# 初始化服务
chat_service = RAGChatService()

# 处理用户问题
response = chat_service.process_message(
    session_id=1,
    user_message="什么是向量数据库?",
    user_id=user.id
)

# 使用向量数据库服务
from chat.service.vector_db_service import VectorDBService

# 初始化向量数据库服务
vector_service = VectorDBService()

# 相似度搜索
results = vector_service.similarity_search(
    query_embedding=query_vector,
    top_k=5
)
```

## 依赖项

- LLM API（如GPT、智谱清言等）
- 向量数据库（如FAISS、Milvus、Chroma等）
- 文本嵌入模型（如OpenAI Embeddings、智谱嵌入等）
- Django会话管理
