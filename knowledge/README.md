# 📚 知识库模块 (Knowledge)

<div align="center">
  <p><strong>知识助手项目的核心知识管理与内容处理子系统</strong></p>
</div>

## 📋 模块简介

知识库模块是知识助手项目的核心组件，负责知识库的创建、文档管理、内容处理和检索服务。该模块实现了文档上传、Markdown内容解析、文本向量化以及基于向量的智能检索功能，为整个系统提供知识支持。

## 🔑 核心功能

- **📂 知识库管理**
  - 知识库创建与分类
  - 知识权限与共享控制
  - 知识统计与分析
  - 版本历史管理

- **📄 文档处理**
  - 多格式文档上传与解析
  - 文档内容提取与分块
  - 文档元数据管理
  - 全文索引构建

- **📝 Markdown支持**
  - Markdown内容解析与渲染
  - 内容结构化处理
  - 代码块与公式支持
  - 图表与媒体元素嵌入

- **🔍 检索服务**
  - 基于向量的相似度搜索
  - 关键词与语义混合检索
  - 上下文感知的问答匹配
  - 搜索结果排序与优化

## 📁 目录结构

```
knowledge/
│
├── models/                 # 模型定义
│   ├── __init__.py         # 模型初始化
│   ├── knowledge_base_models.py # 知识库模型
│   ├── document_models.py  # 文档模型
│   └── markdown_models.py  # Markdown模型
│
├── migrations/             # 数据库迁移文件
├── __init__.py            # 包初始化
├── admin.py               # 管理员配置
├── apps.py                # 应用配置
├── serializers.py         # 序列化器定义
├── urls.py                # URL路由配置
├── views.py               # 视图与API实现
└── tests.py               # 单元测试
```

## 🔌 API 接口

| 接口路径 | 方法 | 描述 | 权限 |
|---------|------|------|------|
| `/api/knowledge/bases/` | GET | 获取知识库列表 | 需认证 |
| `/api/knowledge/bases/` | POST | 创建新知识库 | 需认证 |
| `/api/knowledge/bases/{id}/` | GET/PUT/DELETE | 知识库详情/更新/删除 | 拥有者 |
| `/api/knowledge/documents/` | GET | 获取文档列表 | 需认证 |
| `/api/knowledge/documents/` | POST | 上传新文档 | 需认证 |
| `/api/knowledge/documents/{id}/` | GET/PUT/DELETE | 文档详情/更新/删除 | 拥有者 |
| `/api/knowledge/search/` | POST | 知识库内容检索 | 需认证 |

## 📊 数据模型

### 知识库模型 (KnowledgeBase)
- `name`: 知识库名称
- `description`: 知识库描述
- `owner`: 所有者（外键）
- `created_at`: 创建时间
- `updated_at`: 更新时间
- `is_public`: 是否公开
- `collaborators`: 协作者（多对多）

### 文档模型 (Document)
- `title`: 文档标题
- `knowledge_base`: 所属知识库（外键）
- `file`: 文件路径
- `file_type`: 文件类型
- `uploaded_by`: 上传者（外键）
- `upload_time`: 上传时间
- `size`: 文件大小
- `processed`: 处理状态

### Markdown模型 (Markdown)
- `document`: 关联文档（外键）
- `content`: Markdown内容
- `rendered_html`: 渲染后的HTML
- `toc`: 目录结构
- `last_edited`: 最后编辑时间

## 🧪 测试覆盖

- 知识库CRUD操作测试
- 文档上传与解析测试
- Markdown处理与渲染测试
- 文档检索与问答测试
- 权限控制与安全测试

## 🔗 与其他模块的关联

- 与**账户模块**集成，实现权限控制与用户关联
- 与**聊天模块**集成，提供知识问答支持
- 与**RAG系统**集成，实现检索增强生成功能
