# 📚 知识助手项目 (Knowledge Assistant)

## 🌟 项目介绍

知识助手是一个基于 Django + Django REST Framework 构建的现代化知识管理与问答系统，旨在提供高效、智能的知识库管理和文档检索服务。系统集成了先进的 RAG (检索增强生成) 技术，支持文档上传、Markdown解析、用户管理和智能聊天等功能。通过本系统，用户可以轻松构建自己的知识库，并通过自然语言问答方式快速获取所需信息。

## ✨ 主要功能

- **🔐 用户管理**
  - 用户注册、登录与身份认证
  - 个人资料定制与管理
  - 基于角色的权限控制
  - 安全的密码管理与重置

- **📝 知识库管理**
  - 多知识库创建与维护
  - 支持PDF、Word、Markdown等多种文档格式
  - 文档标签分类与组织
  - 文档版本控制与更新

- **🔍 智能检索与问答**
  - 基于向量的语义检索
  - 上下文感知的问答系统
  - 相关度排序的搜索结果
  - 引用追溯与来源验证

- **💬 交互式聊天**
  - 智能对话与连续会话
  - 会话历史管理与导出
  - 多轮���话上下文保持
  - 实时反馈与建议

- **🧠 RAG技术集成**
  - 检索增强生成技术应用
  - 高质量文本嵌入与向量化
  - 语义理解与精准匹配
  - 知识融合与回答优化

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Django 4.0+
- 向量数据库（如FAISS）
- 文本嵌入模型（如智谱AI嵌入）

### 安装步骤

1. **克隆代码库**
   ```bash
   git clone https://github.com/yourusername/knowledge_assistant.git
   cd knowledge_assistant
   ```

2. **创建并激活虚拟环境（推荐）**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **环境配置**
   - 复制 `.env.example` 为 `.env` 并填写相关配置
   - 配置数据库连接和AI服务API密钥

5. **数据库迁移**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **创建超级用户（可选）**
   ```bash
   python manage.py createsuperuser
   ```

7. **启动服务**
   ```bash
   python manage.py runserver
   ```

8. **访问系统**
   在浏览器中访问 http://localhost:8000/

## 📂 项目结构

```
knowledge_assistant/
│
├── account/            # 用户账户与认证模块
│   ├── models/         # 用户和个人资��模型
│   └── ...
│
├── chat/               # 聊天与对话模块
│   ├── models/         # 会话与消息模型
│   ├── service/        # RAG聊天服务
│   └── ...
│
├── knowledge/          # 知识库管理模块
│   ├── models/         # 知识库与文档模型
│   └── ...
│
├── knowledge_assistant/ # 核心配置
│   ├── settings.py     # 项目设置
│   ├── urls.py         # URL路由
│   ├── vector_store.py # 向量存储实现
│   └── ...
│
├── media/              # 上传文件存储
│   └── documents/      # 文档存储目录
│
├── rag_demo/           # RAG技术演示
│   ├── data/           # 示例数据
│   └── index/          # 生成的索引
│
└── tests/              # 测试代码
```

## 🛠 技术架构

- **后端框架**: Django 4.0, Django REST Framework
- **数据存储**: 
  - 关系型数据库: SQLite (开发), PostgreSQL (生产)
  - 向量数据库: FAISS/Chroma
- **AI组件**: 
  - 文本嵌入: 智谱AI嵌入
  - 大语言模型: 支持多种LLM接口
- **前端技术**: 
  - 可选集成Vue.js/React前端框架
  - 响应式设计支持多终端访问

## 📖 模块说明

每个模块目录都包含详细的README文件，提供该模块的具体功能、API接口和使用说明：

- [账户模块](knowledge_assistant/account/README.md) - 用户管理与认证
- [聊天模块](knowledge_assistant/chat/README.md) - 智能对话与问答
- [知识库模块](knowledge_assistant/knowledge/README.md) - 文档管理与知识组织
- [RAG演示](knowledge_assistant/rag_demo/README.md) - 检索增强生成技术演示

## 🔄 开发工作流

1. 创建功能分支
2. 提交代码更改
3. 运行测试确保无误
4. 提交合并请求
5. 代码审查后合并

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 👥 贡献指南

欢迎提交问题报告和改进建议。对于重大更改，请先创建issue讨论您想要改变的内容。

## 📞 联系方式

如有问题或建议，请通过以下方式联系我们：
- 项目Issue页面
- 电子邮件: example@email.com

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和测试者。
