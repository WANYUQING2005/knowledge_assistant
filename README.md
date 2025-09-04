# 个人知识库助手 · README

一个支持 **私有文档管理 + RAG 智能问答** 的项目。你可上传 PDF/Word/Markdown 等文档，系统自动切分与向量化，基于你的知识库进行问答。

---

## 功能清单
- ✅ 知识库管理（上传/删除/检索/标签）
- ✅ 私人 AI 问答（基于知识库优先回答））
- ⛔ 多模型切换（后续扩展）

---

## 技术栈
- **前端**：React + Vite 
- **后端**：Django + DRF + LangChain
- **向量库**：FAISS（本地）
- **模型**：
  - 向量：智谱 Embedding API
  - LLM：自选（OpenAI / DeepSeek / 智谱GLM 其一）

---

## 目录结构
```bash
project-root
├─ frontend/               # React 前端
├─ backend/                # Django + DRF + LangChain
│  ├─ apps/knowledge/      # 文档、向量、标签等
│  ├─ rag/                 # 检索与生成逻辑
│  └─ settings.py
├─ data/                   # 原始文档与中间文件
├─ index/faiss/            # 向量索引（运行后生成）
├─ scripts/                # 开发辅助脚本
└─ .env                    # 环境变量
```

## 环境准备
coming soon

## demo 运行
coming soon

## 里程碑计划
<img width="1526" height="576" alt="图片" src="https://github.com/user-attachments/assets/890d3e17-87b3-4ddf-8e0b-ad3c1a736a6a" />
