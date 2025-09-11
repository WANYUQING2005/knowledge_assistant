# Knowledge 模块

## 简介

Knowledge模块是知识助手系统的核心组件，负责知识库的创建、管理和维护。该模块处理文档的上传、解析、向量化和索引，支持多种文档格式，提供知识检索的基础架构。

## 目录结构

```
knowledge/
├── migrations/       # 数据库迁移文件
├── models/           # 模型文件目录
│   ├── __init__.py
│   ├── document_models.py  # 文档相关模型
│   └── knowledge_base_models.py  # 知识库相关模型
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

- **知识库管理**：创建、编辑、删除知识库
- **文档管理**：上传、解析、删除文档
- **文档向量化**：将文档内容转换为向量表示
- **知识索引**：构建和维护向量索引
- **标签管理**：对知识库和文档进行分类标记

## API端点

- `/api/knowledge/bases/` - 管理知识库
- `/api/knowledge/bases/{id}/` - 特定知识库操作
- `/api/knowledge/documents/` - 管理文档
- `/api/knowledge/documents/{id}/` - 特定文档操作
- `/api/knowledge/documents/upload/` - 上传新文档
- `/api/knowledge/tags/` - 管理标签

## 使用示例

### 创建知识库
```http
POST /api/knowledge/bases/
Content-Type: application/json
Authorization: Token {user_token}

{
  "name": "Python编程指南",
  "description": "Python编程语言的综合指南和教程集合",
  "is_public": true
}
```

### 上传文档
```http
POST /api/knowledge/documents/upload/
Content-Type: multipart/form-data
Authorization: Token {user_token}

{
  "knowledge_base_id": 1,
  "file": [文件数据],
  "title": "Python基础教程",
  "description": "Python语言入门指南",
  "tags": ["python", "教程", "编程"]
}
```

## 数据模型

### KnowledgeBase模型
表示一个完整的知识库，可以包含多个文档。

### Document模型
表示上传的单个文档，存储文件路径、元数据等信息。

### DocumentChunk模型
表示文档被分割后的文本片段，用于向量存储和检索。

## 支持的文档格式

- PDF文件
- Markdown文档
- Word文档
- 纯文本文件
- HTML网页
- 其他可解析文本格式

## 依赖项

- 文档解析库（如PyPDF2, python-docx等）
- 文本向量化工具
- 向量数据库接口
- 文件存储系统
