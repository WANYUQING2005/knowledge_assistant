# RAG知识库问答系统

## 📖 项目简介

这是一个基于检索增强生成（RAG）技术的智能知识库问答系统。系统支持多种文档格式的导入、智能文档分块、标签生成，并提供基于向量搜索和标签搜索的多种检索方式。

## ✨ 主要功能

### 🔧 核心功能
- **多格式文档支持**: 支持PDF、TXT、DOCX等多种文档格式
- **智能文档分块**: 
  - 🤖 LLM智能语义分块（优先）
  - 📝 Q&A格式分块（回退）
  - ✂️ 字符切分（兜底）
- **自动标签生成**: 基于LLM为每个文档块生成相关标签
- **多种检索方式**:
  - 🔍 向量相似度搜索
  - 🏷️ 基于标签的智能搜索
  - 📊 阈值过滤搜索
- **对话历史**: 支持多轮对话上下文记忆
- **流式输出**: 实时显示AI回答过程

### 🎯 特色功能
- **标签智能匹配**: 使用AI模型匹配用户查询与知识库标签
- **数据库去重**: 基于内容哈希的智能去重机制
- **增量更新**: 支持向量库的增量更新
- **多模型支持**: 集成Gemini AI模型

## 🛠️ 技术架构

### 核心组件
- **LLM模型**: DeepSeek / qwen
- **向量模型**: 智谱AI Embeddings
- **向量数据库**: FAISS
- **关系数据库**: MySQL
- **Web框架**: LangChain

### 目录结构
```
rag_demo/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python依赖包列表
├── start.py                  # 一键启动脚本
├── AiChat.py                 # 主要问答接口
├── tag_search.py             # 基于标签的智能搜索
├── __pycache__/              # Python编译缓存
│   ├── gemini_llm.cpython-310.pyc
│   └── tag_search.cpython-310.pyc
├── data/                     # 文档数据目录
│   ├── git.txt              # Git相关文档
│   ├── intro.txt            # 系统介绍文档
│   ├── pytorch.txt          # PyTorch框架文档
│   ├── MFC的Dlg VS App.txt  # MFC开发相关文档
│   ├── test.pdf             # PDF格式测试文档
│   ├── wrong.txt            # 测试用例文档
│   └── tags.json            # 预设标签配置文件
├── index/                    # 向量索引存储目录
│   └── faiss/               # FAISS向量索引
│       ├── index.faiss      # 向量索引文件
│       └── index.pkl        # 索引元数据文件
└── kb/                       # 知识库核心模块
    ├── __init__.py          # 模块初始化文件
    ├── init_db.py           # 数据库初始化脚本
    ├── clear_db.py          # 数据库清理脚本
    ├── ingest.py            # 文档摄取处理脚本
    ├── llm_chunker.py       # LLM智能分块模块
    ├── embeddings_zhipu.py  # 智谱AI嵌入模型
    ├── loaders.py           # 多格式文档加载器
    └── __pycache__/         # 编译缓存目录
```

## 🚀 快速开始

### 环境要求
- **Python**: 3.8+
- **MySQL**: 5.7+
- **API密钥**: 
  - 有效的OPEN API密钥
  - 有效的智谱AI API密钥

### 安装步骤

#### 1. 克隆项目
```bash
git clone <your-repo-url>
cd rag_demo
```

#### 2. 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 环境配置
在 `.env` 文件中配置环境变量：



#### 4. 一键启动（推荐）
```bash
python start.py
```
这将自动执行环境检查、依赖安装、数据库初始化等步骤。

#### 5. 手动初始化（可选）
如果不使用一键启动脚本，可以手动执行以下步骤：

```bash
# 初始化数据库表结构
cd kb
python init_db.py
cd ..

# 导入文档到知识库
cd kb  
python ingest.py
cd ..
```

## 📚 使用指南

### 1. 💬 基本问答
```bash
# 启动问答系统
python AiChat.py
```

系统功能：
- 🔍 智能检索相关文档片段
- 🤖 使用LLM AI生成综合回答
- 📋 显示答案来源和相似度评分
- 💭 支持多轮对话上下文

### 2. 🏷️ 基于标签的搜索
```bash
# 启动标签搜索系统
python tag_search.py
```

工作流程：
1. 📋 从数据库提取所有标签
2. 🤖 使用AI匹配相关标签
3. 📚 返回匹配标签的所有相关文档块
4. 📊 按相关度排序显示结果

### 3. 🗄️ 数据库管理
```bash
# 清空数据库
cd kb
python clear_db.py
cd ..

# 重新初始化数据库
cd kb
python init_db.py
cd ..

# 重新导入文档
cd kb
python ingest.py
cd ..
```

### 4. 🚀 一键管理
```bash
# 使用启动脚本进行系统管理
python start.py
```

启动脚本提供的功能：
- ✅ 环境检查
- 📦 依赖安装
- 🗄️ 数据库初始化
- 📚 文档导入
- 💬 启动问答系统
- 🏷️ 启动标签搜索

