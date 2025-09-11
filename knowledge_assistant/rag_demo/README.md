# RAG 演示目录

## 简介

RAG（检索增强生成）演示目录包含了一系列脚本和工具，用于展示和测试RAG技术在知识助手系统中的应用。这些示例代码提供了从文档摄入、文本嵌入到问答生成的完整流程演示。

## 目录结构

```
rag_demo/
├── __init__.py           # 包初始化文件
├── embeddings_zhipu.py   # 智谱AI文本嵌入实现
├── ingest.py             # 文档摄入处理脚本
├── llm_chunker.py        # 基于LLM的文本分块工具
├── loaders.py            # 各种文档格式的加载器
├── rag_qa.py             # RAG问答演示脚本
├── tags_search.py        # 基于标签的搜索功能
├── data/                 # 示例数据目录
└── index/                # 生成的索引存储目录
```

## 主要功能

- **文档摄入**：演示如何将各种格式的文档加载、解析和处理
- **文本分块**：展示不同的文本分块策略和实现方法
- **嵌入生成**：使用智谱AI等模型生成文本嵌入向量
- **向量存储**：演示向量数据的存储和索引创建
- **RAG问答**：基于检索和生成的问答流程示例

## 使用示例

### 文档摄入

```bash
python -m rag_demo.ingest --input_dir ./documents --output_dir ./index
```

### 问答测试

```bash
python -m rag_demo.rag_qa --query "Python中的装饰器是什么?" --index_dir ./index
```

## 关键脚本说明

### embeddings_zhipu.py
实现基于智谱AI的文本嵌入功能，将文本转换为向量表示。

### ingest.py
处理文档摄入流程，包括加载文档、分块、生成嵌入、创建索引等步骤。

### llm_chunker.py
使用LLM来智能分割文本，优化检索质量。

### loaders.py
提供各种文档格式的加载器，支持PDF、Markdown、Word等格式。

### rag_qa.py
演示完整的RAG问答流程，从用户问题到生成回答的全过程。

## 依赖项

- 文本嵌入模型（如智谱AI嵌入）
- 大语言模型（LLM）
- 文档处理库（PyPDF2, python-docx等）
- 向量数据库（FAISS等）

## 注意事项

本目录中的代码主要用于演示和测试目的，生产环境中的实现可能需要更多的优化和错误处理。
