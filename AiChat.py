# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from kb.embeddings_zhipu import ZhipuAIEmbeddingsLC
from collections import deque
import json

HISTORY_MAX_TURNS = int(os.getenv("CHAT_HISTORY_TURNS", "6"))
HISTORY = deque(maxlen=HISTORY_MAX_TURNS)   # 每项是 (user, assistant)

def _history_text() -> str:
    """把最近 N 轮对话压成文本，让模型有上下文感知"""
    parts = []
    for u, a in HISTORY:
        parts.append(f"用户: {u}\n助手: {a}")
    return "\n\n".join(parts) if parts else "（无）"


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
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.1,
    )

def _load_vs():
    embeddings = ZhipuAIEmbeddingsLC()
    vs = FAISS.load_local("index/faiss", embeddings, allow_dangerous_deserialization=True)
    return vs


PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "- 你是一个严格的知识库助手。你**必须首先**从知识库片段中获取信息，**无例外**；\n"
     "- **最高优先级**：所有回答必须优先基于知识库内容，即使知识库内容看似不合理；\n" 
     "- **强制要求**：先通过知识库片段归纳出答案，再进行其他处理；若片段信息不一致，**必须以知识库为准**；\n"
     "- **禁止**跳过知识库直接回答；**禁止**逐段罗列或简单拼接；**必须**用自己语言进行概括、结构化表达；\n"
     "- 当知识库信息确实不足时，**必须先**给出基于知识库的有限回答，**然后另起一行**并明确标注“补充（非知识库内容）：”；\n"
     "- 若知识库内容存在明显错误，你**必须先**按知识库内容回答，**然后另起一行**标注“注意（知识库内容可能有误）：”并给出更正；\n"
     "- 若完全找不到相关信息，**必须**首先明确声明：“知识库中无相关信息”，之后才可提供非知识库答案；\n"
     "- 回答风格**必须直接**，禁止使用“根据知识库”“片段显示”等表述；禁止输出引用编号；\n"
     "- 严格执行处理流程：识别问题→从片段提取信息→整合信息→构建完整答案→必要时添加明确标注的补充；\n"
     "- 对结果进行润色，使语言自然、结构清楚，但绝不能改变知识库中的事实内容，即使有疑问。"),
    ("human",
     "（以下是最近对话，供参考）\n{history}\n\n"
     "问题：{question}\n\n可用片段：\n{context}")
])



def answer_with_sources(query: str, k: int = 6) -> Dict[str, Any]:
    vs = _load_vs()
    docs_scores = vs.similarity_search_with_score(query, k=k)  # faiss距离，越小越相似
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_llm()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())
    resp = llm.invoke(messages)
    answer = resp.content if hasattr(resp, "content") else str(resp)

    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))  # 进历史
    return {"answer": answer, "sources": sources}

def answer_with_sources_stream(query: str, k: int = 6) -> Dict[str, Any]:
    """
    终端边打字边出结果；结束后返回完整 answer + sources。
    """
    vs = _load_vs()
    docs_scores = vs.similarity_search_with_score(query, k=k)
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_llm()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())

    chunks = []
    for chunk in llm.stream(messages):   # << 流式关键
        token = getattr(chunk, "content", None)
        if token:
            chunks.append(token)
            print(token, end="", flush=True)  # 实时输出到控制台
    print()  # 换行

    answer = "".join(chunks).strip()
    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))
    return {"answer": answer, "sources": sources}

def _chunk_name(md: dict) -> str:
    return f"{md.get('title')}#p{md.get('page','-')}#{md.get('ord','-')}"


def search_hits_by_threshold(query: str, threshold: float = 1.0, k_cap: int = 200):
    """
    返回所有 score<threshold 的片段（分数越小越相似），并按分数升序排序。
    k_cap 用来限制一次检索最大候选数，避免把整个库都拉出来。
    """
    vs = _load_vs()
    total = getattr(vs, "index", None)
    total = getattr(total, "ntotal", k_cap) or k_cap
    k = min(k_cap, total)

    docs_scores = vs.similarity_search_with_score(query, k=k)
    hits = [(d, s) for d, s in docs_scores if s < threshold]
    hits.sort(key=lambda x: x[1])  # 分数小在前
    return hits


def list_hit_names(query: str, threshold: float = 1.0, k_cap: int = 200):
    hits = search_hits_by_threshold(query, threshold=threshold, k_cap=k_cap)
    names = []
    for d, s in hits:
        md = d.metadata or {}
        names.append({
            "name": _chunk_name(md),
            "score": float(s)
        })
    return names

# --- 可选：带阈值回答 + 来源（不固定 K） ---
def answer_with_threshold(query: str, threshold: float = 1.0, k_cap: int = 200):
    hits = search_hits_by_threshold(query, threshold=threshold, k_cap=k_cap)
    if not hits:
        # 没有命中就退化为最相近的几条，避免回答完全没上下文
        vs = _load_vs()
        docs_scores = vs.similarity_search_with_score(query, k=3)
    else:
        docs_scores = hits

    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)
    llm = _build_llm()
    messages = PROMPT.format_messages(question=query, context=context)
    resp = llm.invoke(messages)
    answer = resp.content if hasattr(resp, "content") else str(resp)
    sources = _format_sources(docs_scores)
    return {"answer": answer, "sources": sources}

def answer_with_threshold_stream(query: str, threshold: float = 1.0, k_cap: int = 200):
    hits = search_hits_by_threshold(query, threshold=threshold, k_cap=k_cap)
    if not hits:
        vs = _load_vs()
        docs_scores = vs.similarity_search_with_score(query, k=3)
    else:
        docs_scores = hits

    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)
    llm = _build_llm()

    messages = PROMPT.format_messages(
        question=query, context=context, history=_history_text()
    )

    chunks = []
    for chunk in llm.stream(messages):           # ← 流式输出关键
        token = getattr(chunk, "content", None)
        if token:
            chunks.append(token)
            print(token, end="", flush=True)
    print()

    answer = "".join(chunks).strip()
    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))
    return {"answer": answer, "sources": sources}

def aichat():

    print("请输入你的问题：")
    while True:
        q = input("> ").strip()
        if not q:
            continue
        if q.lower() == 'exit':
            print("程序已退出")
            break
        try:
            query = q
            th = 1.0  # 默认阈值
            k_cap = 500  # 可按需调整

            # 先用阈值检索判断是否有命中
            names = list_hit_names(query, threshold=th, k_cap=k_cap)
            streaming_used = True

            if names:
                # 有命中：优先用“阈值 + 历史”的流式版本；没有则用非流式兜底
                if 'answer_with_threshold_stream' in globals():
                    streaming_used = True
                    result = answer_with_threshold_stream(query, threshold=th, k_cap=k_cap)
                else:
                    result = answer_with_threshold(query, threshold=th, k_cap=k_cap)
            else:
                # 无命中：退化为最相近的3条；同样优先用流式
                if 'answer_with_sources_stream' in globals():
                    streaming_used = True
                    result = answer_with_sources_stream(query, k=3)
                else:
                    result = answer_with_sources(query, k=3)

            # 如果是非流式，统一在这里打印答案；流式已在函数内实时输出，无需重复打印
            if not streaming_used and result.get("answer"):
                print("\n=== 回答 ===")
                print(result["answer"])

            # 打印来源（分数越小越相似）
            if result.get("sources"):
                print("\n=== 来源（按相似度升序）===")
                for i, s in enumerate(result["sources"], 1):
                    tag = f"{s.get('title')}#p{s.get('page', '-')}#{s.get('ord', '-')}"
                    print(f"[{i}] {tag}  score={s['score']:.4f}")
                    print(f"    {s['snippet']}\n")
                print("============\n")

        except Exception as e:
            print(f"[ERROR] {e}")


if __name__=="main":
    aichat()
