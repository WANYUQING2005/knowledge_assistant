# 🧠 RAG演示模块 (rag_demo)

<div align="center">
  <p><strong>检索增强生成技术的实现与演示</strong></p>
</div>

## 📋 模块简介

RAG演示模块提供了检索增强生成(Retrieval-Augmented Generation)技术的完整实现示例。该模块包含文档加载、文本分块、向量嵌入、索引构建和智能问答等功能，展示了如何结合大型语言模型与知识库来提高回答质量和准确性。

## 🔑 核心功能

- **📥 数据加载与处理**
  - 多格式文档加载器
  - 文本内容提取与清洗
  - 元数据管理与处理
  - 批量数据导入

- **✂️ 文本分块**
  - 智能文本分段
  - 上下文窗口维护
  - 语义完整性保证
  - 可配置的分块策略

- **🔢 向量嵌入**
  - 基于智谱AI的文本向量化
  - 高维向量生成与管理
  - 批量嵌入处理
  - 多模型支持与配置

- **🔍 向量索引**
  - FAISS向量数据库集成
  - 高效相似度搜索
  - 索引持久化与加载
  - 索引优化与配置

- **❓ 问答生成**
  - 基于检索的上下文生成
  - 大型语言模型集成
  - 问题分析与理解
  - 回答质量评估与优化

## 📁 目录结构

```
rag_demo/
│
├── __init__.py           # 包初始化
├── embeddings_zhipu.py   # 智谱AI向量嵌入实现
├── ingest.py             # 数据入库处理脚本
├── llm_chunker.py        # 基于大模型的文本分块器
├── loaders.py            # 文档加载器实现
├── rag_qa.py             # RAG问答主逻辑
├── tags_search.py        # 标签检索实现
│
├── data/                 # 测试数据目录
│   ├── git.txt           # Git相关测试文本
│   ├── intro.txt         # 介绍文本
│   └── wrong.txt         # 错误示例文本
│
└── index/                # 索引存储目录
    └── faiss/            # FAISS向量索引文件
```

## 🚀 使用说明

### 数据导入
```python
# 导入测试文档到向量数据库
python -m rag_demo.ingest --input rag_demo/data/ --output rag_demo/index/
```

### 问答交互
```python
# 使用RAG模型进行问答
python -m rag_demo.rag_qa --index rag_demo/index/faiss/ --query "什么是Git?"
```

### 标签搜索
```python
# 基于标签进行检索
python -m rag_demo.tags_search --index rag_demo/index/faiss/ --tags "git,版本控制"
```

## 💡 工作原理

1. **数据处理流程**：
   - 文档加载 → 文本提取 → 文本分块 → 向量嵌入 → 索引构建

2. **查询处理流程**：
   - 问题分析 → 向量化 → 相似度检索 → 上下文构建 → 大模型生成 → 回答优化

3. **核心算法**：
   - 使用智谱AI embedding-2进行文本向量化
   - 采用递归特征分块保持文本语义完整性
   - 基于FAISS实现高效向量相似度搜索
   - 通过上下文增强提高大模型回答质量

## 🔗 与其他模块的关联

- 与**知识库模块**集成，提供智能检索能力
- 为**聊天模块**提供基于知识库的问答支持
- 通过**主配置模块**获取系统级设置和参数
