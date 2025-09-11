# -*- coding: utf-8 -*-
"""
在不更改现有函数名、变量名、返回值结构的前提下：
- 保留对话历史
- 增加阈值检索/流式回答
- 保留原有 kb_id 元数据过滤功能
- 新增目录切换模式选择不同知识库索引
"""
import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from collections import deque

from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
global CURRENT_KB_ID

# 增加异常处理的导入方式，适应不同的调用场景
try:
    # 当作为包的一部分被导入时
    from .embeddings_zhipu import ZhipuAIEmbeddingsLC
except (ImportError, ValueError):
    try:
        # 当在相同目录下导入时
        from embeddings_zhipu import ZhipuAIEmbeddingsLC
    except ImportError:
        # 当从不同路径导入时
        from knowledge_assistant.rag_demo.embeddings_zhipu import ZhipuAIEmbeddingsLC


load_dotenv()

# -------------------- 环境与历史 --------------------
HISTORY_MAX_TURNS = int(os.getenv("CHAT_HISTORY_TURNS", "6"))
HISTORY: deque = deque(maxlen=HISTORY_MAX_TURNS)

# 知识库选择模式
KB_SELECTION_MODE = os.getenv("KB_SELECTION_MODE", "metadata")  # "metadata" | "dir"
KB_DIR_PATTERN = os.getenv("KB_DIR_PATTERN", "index/{kb_id}/faiss")
CURRENT_KB_ID = "0"


def _initialize_environment():
    load_dotenv()


def _history_text() -> str:
    parts = []
    for u, a in HISTORY:
        parts.append(f"用户: {u}\n助手: {a}")
    return "\n\n".join(parts) if parts else "（无）"


# -------------------- 向量数据库 --------------------

def _load_vector_store():
    embeddings = ZhipuAIEmbeddingsLC()

    # 使用绝对路径替代相对路径
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 构建到索引文件的绝对路径
    if KB_SELECTION_MODE == "dir" and CURRENT_KB_ID != "0":
        rel_path = KB_DIR_PATTERN.format(kb_id=CURRENT_KB_ID)
        path = os.path.join(base_dir, rel_path)
    else:
        path = os.path.join(base_dir, "index", "faiss")

    # 确保路径存在
    if not os.path.exists(path):
        raise FileNotFoundError(f"FAISS索引路径不存在: {path}")

    vs = FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)
    return vs


# -------------------- 检索逻辑 --------------------

def _search_relevant_docs(vs, query: str, k: int = 6, kb_id: str = "0") -> List[Tuple[Document, float]]:
    docs_scores = vs.similarity_search_with_score(query, k=k)

    if KB_SELECTION_MODE == "metadata" and kb_id != "0":
        filtered_docs_scores = [(doc, score) for doc, score in docs_scores if (doc.metadata or {}).get("kb_id") == kb_id]
        if len(filtered_docs_scores) < k:
            more_docs_scores = vs.similarity_search_with_score(query, k=k * 2)
            filtered_docs_scores = [(doc, score) for doc, score in more_docs_scores if (doc.metadata or {}).get("kb_id") == kb_id]
        docs_scores = filtered_docs_scores

    return docs_scores


def search_hits_by_threshold(vs, query: str, threshold: float = 1.0, k_cap: int = 200, kb_id: str = "0"):
    total = getattr(getattr(vs, "index", None), "ntotal", k_cap) or k_cap
    k = min(k_cap, total)

    docs_scores = vs.similarity_search_with_score(query, k=k)
    hits: List[Tuple[Document, float]] = []
    for d, s in docs_scores:
        md = d.metadata or {}
        if KB_SELECTION_MODE == "metadata" and kb_id != "0" and md.get("kb_id") != kb_id:
            continue
        if s < threshold:
            hits.append((d, s))

    hits.sort(key=lambda x: x[1])
    return hits


def list_hit_names(vs, query: str, threshold: float = 1.0, k_cap: int = 200, kb_id: str = "0"):
    hits = search_hits_by_threshold(vs, query, threshold=threshold, k_cap=k_cap, kb_id=kb_id)
    names: List[Dict[str, Any]] = []
    for d, s in hits:
        md = d.metadata or {}
        names.append({
            "name": f"{md.get('title')}#p{md.get('page','-')}#{md.get('ord','-')}",
            "score": float(s),
        })
    return names


# -------------------- LLM 与上下文 --------------------

def _format_docs_for_llm(docs: List[Document]) -> str:
    lines = []
    for i, d in enumerate(docs, 1):
        md = d.metadata or {}
        tag = f"{md.get('title','?')}#p{md.get('page','-')}#{md.get('ord','-')}"
        snippet = (d.page_content or "").strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + "…"
        lines.append(f"[{i}|{tag}] {snippet}")
    return "\n\n".join(lines)


def _build_language_model():
    return ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.2,
    )


def _format_sources(docs_scores: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
    out = []
    for d, score in docs_scores:
        md = d.metadata or {}
        text = (d.page_content or "").strip()
        out.append({
            "title": md.get("title"),
            "source": md.get("source"),
            "page": md.get("page"),
            "ord": md.get("ord"),
            "kb_id": md.get("kb_id", "0"),
            "score": float(score),
            "snippet": (text[:240] + "…") if len(text) > 240 else text,
        })
    out.sort(key=lambda x: x["score"])
    return out


PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "- 你是一个知识库助手，优先根据给你提供的知识库知识作为主要参考内容；"
     "- **最重要的，**你必须严格按照知识库的内容来回答，即使你认为知识库内容有误，也要按照知识库输出,但是要说明知识库内容有误；"
     "- 如果知识库中没有足够信息，你可以根据自己的信息回答问题，但必须要注明“该回答来自非知识库知识”；"
  #   "- 如果你也无法回答，请说明“无法从知识库和非知识库中找到相关信息”；"
  #   "- **同样重要的是，**如果知识库知识中没有相关信息，可以简短说明没有找到相关信息，不要编造答案；"
     "- 回答时请用直接的口吻，不要出现第三人称口吻，不要出现“根据知识库知识”等内容；"
     "- 如果知识库的内容和非知识库的内容冲突，必须优先使用知识库的内容回答；"
     "- 注意不要出现片段的引用编号；"
     "- 你的回答应该直接简洁明了，不要过多赘述。"),
    ("human", "（以下是最近对话，供参考）\n{history}\n\n问题：{question}\n\n可用片段：\n{context}")
])


# -------------------- 主功能 --------------------
def rag_answer_with_sources(query: str, kb_id: str = "0", k: int = 6) -> Dict[str, Any]:
    global CURRENT_KB_ID
    CURRENT_KB_ID = kb_id

    _initialize_environment()
    vector_store = _load_vector_store()

    docs_scores = _search_relevant_docs(vector_store, query, k, kb_id)
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_language_model()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())
    resp = llm.invoke(messages)
    answer = resp.content if hasattr(resp, "content") else str(resp)

    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))

    return {"answer": answer, "sources": sources}


def rag_answer_with_sources_stream(query: str, kb_id: str = "0", k: int = 6) -> Dict[str, Any]:
    global CURRENT_KB_ID
    CURRENT_KB_ID = kb_id

    _initialize_environment()
    vector_store = _load_vector_store()

    docs_scores = _search_relevant_docs(vector_store, query, k, kb_id)
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_language_model()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())

    chunks: List[str] = []
    for chunk in llm.stream(messages):
        token = getattr(chunk, "content", None)
        if token:
            chunks.append(token)
            print(token, end="", flush=True)
    print()

    answer = "".join(chunks).strip()
    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))
    return {"answer": answer, "sources": sources}


def rag_answer_with_threshold(query: str, kb_id: str = "0", threshold: float = 1.0, k_cap: int = 200) -> Dict[str, Any]:
    global CURRENT_KB_ID
    CURRENT_KB_ID = kb_id

    _initialize_environment()
    vector_store = _load_vector_store()

    hits = search_hits_by_threshold(vector_store, query, threshold=threshold, k_cap=k_cap, kb_id=kb_id)
    docs_scores = hits if hits else _search_relevant_docs(vector_store, query, k=3, kb_id=kb_id)

    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)

    llm = _build_language_model()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())
    resp = llm.invoke(messages)
    answer = resp.content if hasattr(resp, "content") else str(resp)

    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))
    return {"answer": answer, "sources": sources}


def rag_answer_with_threshold_stream(query: str, kb_id: str = "0", threshold: float = 1.0, k_cap: int = 200) -> Dict[str, Any]:
    global CURRENT_KB_ID
    CURRENT_KB_ID = kb_id

    _initialize_environment()
    vector_store = _load_vector_store()

    hits = search_hits_by_threshold(vector_store, query, threshold=threshold, k_cap=k_cap, kb_id=kb_id)

    # 检查是否存在匹配阈值的文档
    has_threshold_hits = len(hits) > 0

    # 获取文档，如果没有匹配阈值的文档，则使用空文档列表，不再进行普通相似度搜索
    docs_scores = hits if has_threshold_hits else []

    docs = [d for d, _ in docs_scores]

    # 如果没有匹配阈值的文档，添加说明
    if not has_threshold_hits:
        context = "知识库中没有匹配的片段。\n\n"
    else:
        context = ""

    # 添加文档内容到上下文
    context += _format_docs_for_llm(docs)

    llm = _build_language_model()
    messages = PROMPT.format_messages(question=query, context=context, history=_history_text())

    chunks: List[str] = []
    for chunk in llm.stream(messages):
        token = getattr(chunk, "content", None)
        if token:
            chunks.append(token)
            print(token, end="", flush=True)
    print()

    answer = "".join(chunks).strip()
    sources = _format_sources(docs_scores)
    HISTORY.append((query, answer))
    return {"answer": answer, "sources": sources}


# -------------------- CLI --------------------
if __name__ == "__main__":
    print("RAG问答系统（Ctrl+C 退出）：")
    try:
        while True:
            user_query = input("请输入你的问题：").strip()
            if not user_query:
                continue

            kb_input = input("请输入知识库ID（默认为0，表示全筛选）：").strip()
            kb_id = kb_input if kb_input else "0"

            th = float(os.getenv("RETRIEVE_THRESHOLD", "1.0"))
            k_cap = int(os.getenv("RETRIEVE_K_CAP", "500"))


            CURRENT_KB_ID = kb_id
            vs = _load_vector_store()
            names = list_hit_names(vs, user_query, threshold=th, k_cap=k_cap, kb_id=kb_id)

            if names:
                result = rag_answer_with_threshold_stream(user_query, kb_id=kb_id, threshold=th, k_cap=k_cap)
            else:
                result = rag_answer_with_sources_stream(user_query, kb_id=kb_id, k=3)

            print("\n=== 回答 ===")
            print(result["answer"])

            print("\n=== 命中片段（按相似度升序）===")
            for i, s in enumerate(result["sources"], 1):
                tag = f"{s.get('title')}#p{s.get('page','-')}#{s.get('ord','-')}[KB:{s.get('kb_id','0')}]"
                print(f"[{i}] {tag}  score={s['score']:.4f}")
                print(f"    {s.get('snippet','')}\n")
            print("============\n")

    except KeyboardInterrupt:
        print("\n程序已退出。")
