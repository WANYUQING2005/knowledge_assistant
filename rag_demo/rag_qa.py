# -*- coding: utf-8 -*-
import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from embeddings_zhipu import ZhipuAIEmbeddingsLC

# 加载环境变量
def _initialize_environment():
    load_dotenv()

# 加载向量数据库
def _load_vector_store():
    embeddings = ZhipuAIEmbeddingsLC()
    vs = FAISS.load_local("index/faiss", embeddings, allow_dangerous_deserialization=True)
    return vs

# 向量检索找到与查询最相关的文档
def _search_relevant_docs(vs, query: str, k: int = 6, kb_id: str = "0") -> List[Tuple[Document, float]]:
    # 取更“稳”的接口：返回相似度分数（faiss距离，越小越相似）
    docs_scores = vs.similarity_search_with_score(query, k=k)
    
    # 根据kb_id筛选文档
    if kb_id != "0":
        # 过滤出kb_id匹配的文档
        filtered_docs_scores = [(doc, score) for doc, score in docs_scores if doc.metadata.get("kb_id") == kb_id]
        
        # 如果过滤后的文档数量少于k，尝试获取更多文档
        if len(filtered_docs_scores) < k:
            # 获取更多文档（k的2倍）进行筛选
            more_docs_scores = vs.similarity_search_with_score(query, k=k*2)
            filtered_docs_scores = [(doc, score) for doc, score in more_docs_scores if doc.metadata.get("kb_id") == kb_id]
        
        docs_scores = filtered_docs_scores
        
    # 确保返回所有匹配的文档，即使少于k个
    return docs_scores

# 将检索到的文档格式化为LLM可用的上下文
def _format_docs_for_llm(docs: List[Document]) -> str:
    lines = []
    for i, d in enumerate(docs, 1):
        md = d.metadata or {}
        tag = f"{md.get('title','?')}#p{md.get('page','-')}#{md.get('ord','-')}"
        snippet = d.page_content.strip()
        if len(snippet) > 800:
            snippet = snippet[:800] + "…"
        lines.append(f"[{i}|{tag}] {snippet}")
    return "\n\n".join(lines)

# 构建语言模型实例
def _build_language_model():
    return ChatOpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        model="deepseek-chat",
        temperature=0.2,
    )

# 格式化来源信息
def _format_sources(docs_scores: List[Tuple[Document, float]]) -> List[Dict[str, Any]]:
    out = []
    for d, score in docs_scores:
        md = d.metadata or {}
        out.append({
            "title": md.get("title"),
            "source": md.get("source"),
            "page": md.get("page"),
            "ord": md.get("ord"),
            "kb_id": md.get("kb_id", "0"),
            "score": float(score),
            "snippet": (d.page_content.strip()[:240] + "…") if len(d.page_content) > 240 else d.page_content.strip()
        })
    # 分数越小越相似：从小到大排序
    out.sort(key=lambda x: x["score"])
    return out

# 定义提示词模板
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

# 主函数：处理问答请求并返回结果
def rag_answer_with_sources(query: str, kb_id: str = "0", k: int = 6) -> Dict[str, Any]:
    """
    使用RAG技术回答用户问题并提供来源信息
    
    参数:
        query (str): 用户输入的问题
        kb_id (str): 知识库ID，默认为"0"表示不按知识库筛选
        k (int): 检索的文档数量，默认为6
        
    返回:
        Dict[str, Any]: 包含回答和来源信息的字典
    """
    # 1. 初始化环境
    _initialize_environment()
    
    # 2. 加载向量数据库
    vector_store = _load_vector_store()
    
    # 3. 使用向量检索找到与查询最相关的k个文档
    docs_scores = _search_relevant_docs(vector_store, query, k, kb_id)
    
    # 4. 将检索到的文档格式化为LLM可用的上下文
    docs = [d for d, _ in docs_scores]
    context = _format_docs_for_llm(docs)
    
    # 5. 构建语言模型实例
    llm = _build_language_model()
    
    # 6. 使用提示词模板和上下文调用大语言模型
    messages = PROMPT.format_messages(question=query, context=context)
    resp = llm.invoke(messages)  # ChatMessage
    answer = resp.content if hasattr(resp, "content") else str(resp)
    
    # 7. 格式化来源信息
    sources = _format_sources(docs_scores)
    
    # 8. 返回包含回答和来源的字典
    return {"answer": answer, "sources": sources}

if __name__ == "__main__":
    # 示例用法
    print("RAG问答系统示例（Ctrl+C 退出）：")
    try:
        while True:
            user_query = input("请输入你的问题：").strip()
            if not user_query:
                continue
            
            # 获取kb_id
            kb_input = input("请输入知识库ID（默认为0，表示不筛选）：").strip()
            kb_id = kb_input if kb_input else "0"
            
            # 调用主函数
            result = rag_answer_with_sources(user_query, kb_id=kb_id, k=3)
            
            # 打印结果
            print("\n=== 回答 ===")
            print(result["answer"])
            print("\n=== 命中片段（按相似度升序）===")
            for i, s in enumerate(result["sources"], 1):
                tag = f"{s.get('title')}#p{s.get('page','-')}#{s.get('ord','-')}[KB:{s.get('kb_id','0')}]"
                print(f"[{i}] {tag}  score={s['score']:.4f}")
                print(f"    {s['snippet']}\n")
            print("============\n")
    except KeyboardInterrupt:
        print("\n程序已退出。")