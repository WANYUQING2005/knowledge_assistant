# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from embeddings_zhipu import ZhipuAIEmbeddingsLC

load_dotenv()

def _format_docs_for_llm(docs: List[Document]) -> str:
    # 给 LLM 的上下文：简短、编号，便于引用
    lines = []
    for i, d in enumerate(docs, 1):
        md = d.metadata or {}
        tag = f"{md.get('title','?')}#p{md.get('page','-')}#{md.get('ord','-')}"
        snippet = d.page_content.strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + "…"
        lines.append(f"[{i}|{tag}] {snippet}")
    return "\n\n".join(lines)

def _format_sources(docs_scores: List[Tuple[Any, float]]) -> List[Dict[str, Any]]:
    # 给前端/命令行展示的结构化来源（包含相似度分数）
    out = []
    for d, score in docs_scores:
        md = d.metadata or {}
        out.append({
            "title": md.get("title"),
            "source": md.get("source"),
            "page": md.get("page"),
            "ord": md.get("ord"),
            "score": float(score),
            "snippet": (d.page_content.strip()[:240] + "…") if len(d.page_content) > 240 else d.page_content.strip()
        })
    # 分数越小越相似：从小到大排序
    out.sort(key=lambda x: x["score"])
    return out

def _build_llm():
    return ChatOpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        model="deepseek-chat",
        temperature=0.2,
    )

def _load_vs():
    embeddings = ZhipuAIEmbeddingsLC()
    vs = FAISS.load_local("index/faiss", embeddings, allow_dangerous_deserialization=True)
    return vs


PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "- 你是一个知识库助手，优先根据给你提供的知识库知识作为主要参考内容；"
     "- **最重要的，**你必须严格按照知识库的内容来回答，即使你认为知识库内容有误，也要按照知识库输出；"
     "- 如果知识库中没有足够信息，你可以根据自己的信息回答问题，但必须要注明“该回答来自非知识库知识”；"
     "- 如果你也无法回答，请说明“无法从知识库和非知识库中找到相关信息”；"
     "- **同样重要的是，**如果知识库知识中没有相关信息，可以简短说明没有找到相关信息，不要编造答案；"
     "- 回答时请用直接的口吻，不要出现第三人称口吻，不要出现“根据知识库知识”等内容；"
     "- 如果知识库的内容和非知识库的内容冲突，必须优先使用知识库的内容回答；"
     "- 注意不要出现片段的引用编号；"
     "- 你的回答应该直接简洁明了，不要过多赘述。"),
    ("human", "问题：{question}\n\n可用片段：\n{context}")
])

def answer_with_sources(query: str, k: int = 6) -> Dict[str, Any]:
    vs = _load_vs()
    # 取更“稳”的接口：返回相似度分数（faiss距离，越小越相似）
    docs_scores = vs.similarity_search_with_score(query, k=k)
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_llm()
    messages = PROMPT.format_messages(question=query, context=context)
    resp = llm.invoke(messages)  # ChatMessage
    answer = resp.content if hasattr(resp, "content") else str(resp)

    sources = _format_sources(docs_scores)
    return {"answer": answer, "sources": sources}

if __name__ == "__main__":
    print("请输入你的问题（Ctrl+C 退出）：")
    try:
        while True:
            q = input("> ").strip()
            if not q:
                continue
            result = answer_with_sources(q, k=3)
            print("\n=== 回答 ===")
            print(result["answer"])
            print("\n=== 命中片段（按相似度升序）===")
            for i, s in enumerate(result["sources"], 1):
                tag = f"{s.get('title')}#p{s.get('page','-')}#{s.get('ord','-')}"
                print(f"[{i}] {tag}  score={s['score']:.4f}")
                print(f"    {s['snippet']}\n")
            print("============\n")
    except KeyboardInterrupt:
        print("\nBye.")
