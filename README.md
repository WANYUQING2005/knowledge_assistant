# 📚 知识助手项目 (Knowledge Assistant)


## 🌟 项目介绍

知识助手是一个基于 Django + Django REST Framework 构建的现代化知识管理与问答系统，旨在提供高效、智能的知识库管理和文档检索服务。系统集成了先进的 RAG (检索增强生成) 技术，支持文档上传、Markdown解析、用户管理和智能聊天等功能。

## ✨ 主要功能

- **🔐 用户管理**
  - 用户注册、登录与认证
  - 个人资料管理
  - 权限控制与安全保障

- **📝 知识库管理**
  - 知识库创建与维护
  - 支持多种文档格式上传
  - Markdown内容解析与渲染

- **🔍 检索与问答**
  - 文档智能检索
  - 基于向量搜索的问答系统
  - 上下文相关的回答生成

- **💬 聊天模块**
  - 实时聊天功能
  - 历史记录保存
  - 智能回复

- **🧠 RAG技术集成**
  - 检索增强生成
  - 文本嵌入与向量化
  - 精确的文档匹配与知识提取

## 🚀 安装与运行

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

4. **数据库迁移**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **启动服务**
   ```bash
   python manage.py runserver
   ```

6. **访问系统**
   在浏览器中访问 http://localhost:8000/

## 📂 目录结构

```
knowledge_assistant/
│
├── account/            # 用户与个人资料相关模块
├── chat/               # 聊天相关模块
├── knowledge/          # 知识库与文档相关模块
├── knowledge_assistant/ # Django主配置
│   ├── settings.py     # 项目配置
│   ├── urls.py         # URL路由
│   └── vector_store.py # 向量存储实现
├── media/              # 上传文件存储
├── rag_demo/           # RAG相关示例脚本
├── schedule/           # 项目进度和里程碑文档
└── tests/              # 测试脚本
```

## 🛠 技术栈

- **后端框架**: Django, Django REST Framework
- **数据库**: SQLite (开发), PostgreSQL (生产)
- **AI模型**: RAG (检索增强生成)
- **向量数据库**: FAISS
- **前端**: HTML, CSS, JavaScript (可选与前端框架集成)

## 📖 使用说明

详细的API文档和使用说明请参考各子目录的 README.md 文件。

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 👥 贡献

欢迎提交问题和拉取请求。对于重大更改，请先打开一个问题讨论您想要改变的内容。

