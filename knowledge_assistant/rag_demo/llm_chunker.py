import os
import os
import json
from typing import List, Dict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

load_dotenv()

_DEF_WIN = int(os.getenv("LLM_CHUNK_WINDOW", "3000"))

_SCHEMA = (
    "严格返回 JSON 数组，每个元素形如：{\n"
    "  \"chunk\": \"字符串，单个分块内容，长度不超过 MAX_LEN 字符，避免截断句子\",\n"
    "  \"tags\": [\"自行根据语义设置标签\"]\n"
    "}。不要输出注释、解释或其它非 JSON 内容。"
)

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是专业的文本整理助手：将给定中文或英文长文本进行**语义分块**，并为每个分块自动生成 1–3 个最相关的标签。\n"
     "\n"
     "具体要求：\n"
     "1. 分块规则：\n"
     "   - 分块应尽量保持语义完整，避免在句中硬切。\n"
     "   - 如果自然段过长，可以在句号、分号、逗号等自然停顿处切分。\n"
     "   - 每个分块的最大长度为 MAX_LEN 字符。\n"
     "   - 同一分块内部的语义要相对单一、集中，不能混合多个无关主题。\n"
     "\n"
     "2. 标签生成：\n"
     "   - 每个分块必须生成 1–3 个标签。\n"
     "   - **请自行创建标签**，而不是从给定的候选标签中选择。\n"
     "   - 标签需紧扣该分块的核心主题，避免过于宽泛或抽象。\n"
     "   - 标签用简短词语（1–4 个字/词），不可用完整句子。\n"
     "   - 分块内部语义应保持一致，确保该块整体内容能被所选标签统一概括。\n"
     "   - 标签应覆盖不同层级：优先选择能代表**主题/话题**的词，如果有关键对象或动作，也可作为标签。\n"
     "\n"
     "3. 其他要求：\n"
     "   - 分块与标签之间必须一一对应。\n"
     "   - 即使内容模糊，也要尽量生成最接近的标签。\n"
     "- 输出格式：{schema}"),
    ("human",
     "以下仅供参考的标签例子（你可以创建完全不同的标签）：\n{tag_list}\n\nMAX_LEN={max_len}\n\n原始文本：\n{window_text}\n\n请直接给出 JSON 数组结果。")
])


def _build_llm():
    # 优先尝试使用智谱AI API配置
    return ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.2,
    )


def load_tag_candidates() -> List[str]:
    # 1) 优先：环境变量 JSON 字符串
    env_json = os.getenv("TAG_SET_JSON")
    if env_json:
        try:
            tags = json.loads(env_json)
            if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
                return tags
        except Exception:
            pass
    # 2) 文件：默认 data/tags.json
    path = os.getenv("TAGS_PATH", "data/tags.json")
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                tags = json.load(f)
            if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
                return tags
        except Exception:
            pass
    # 3) 兜底：给一组通用标签
    return ["通用", "定义", "背景", "原理", "步骤", "参数", "示例", "注意事项", "限制", "性能", "对比", "引用", "FAQ"]


def _windows(text: str, win_chars: int) -> List[str]:
    # 简单基于段落累积，尽量不拆句
    paras = [p for p in text.split("\n\n") if p.strip()]
    out, buf = [], []
    count = 0
    for p in paras:
        l = len(p)
        if count + l + 2 <= win_chars:
            buf.append(p)
            count += l + 2
        else:
            if buf:
                out.append("\n\n".join(buf))
            buf = [p]
            count = l
    if buf:
        out.append("\n\n".join(buf))
    return out or [text]


def _safe_parse(json_str: str) -> List[Dict]:
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    # 简单修复：截断到最后一个闭合方括号
    last = json_str.rfind("]")
    if last != -1:
        try:
            return json.loads(json_str[:last+1])
        except Exception:
            return []
    return []


def llm_chunk_and_tag(text: str, tag_candidates: List[str], max_chunk_chars: int,
                      source: str, title: str) -> List[Document]:
    text = (text or "").strip()
    if not text:
        return []
    print("llm_chunk_and_tag输入",text)
    print("进入llm_chunk_and_tag")
    llm = _build_llm()
    
    # 检查 LLM 是否初始化成功，如果失败则使用简单的字符分块作为回退
    if llm is None:
        print("[WARN] LLM 初始化失败，使用简单字符分块作为回退")
        return _fallback_chunking(text, max_chunk_chars, source, title, tag_candidates)
    
    windows = _windows(text, int(os.getenv("LLM_CHUNK_WINDOW", _DEF_WIN)))
    print(f"windows数量: {len(windows)}")
    print("windows内容:")
    for i, window in enumerate(windows):
        print(f"窗口 {i+1}:\n{window}")
        print(f"窗口 {i+1} 长度: {len(window)}")
        print("---")
    
    results: List[Document] = []
    ord_idx = 0
    tag_list = "\n".join(f"- {t}" for t in tag_candidates)
    
    try:
        for w in windows:
            messages = PROMPT.format_messages(tag_list=tag_list, max_len=max_chunk_chars, window_text=w, schema=_SCHEMA)
            
            try:
                # 调用 LLM API
                resp = llm.invoke(messages)
                content = resp.content if hasattr(resp, "content") else str(resp)
                print(f"LLM 返回的原始内容: {content}")
                data = _safe_parse(content)
                print(f"解析后的数据: {data}")
                
                # 处理 LLM 返回的结果
                if not data:
                    print(f"[WARN] LLM 返回的解析结果为空，窗口长度: {len(w)}")
                    # 对于解析失败的窗口，使用简单的字符分块作为回退
                    fallback_chunks = _fallback_chunking_for_window(w, max_chunk_chars, source, title, tag_candidates, ord_idx)
                    results.extend(fallback_chunks)
                    ord_idx += len(fallback_chunks)
                    continue
                
                # 处理有效的分块结果
                for item in data:
                    chunk = (item.get("chunk") or "").strip()
                    tags = item.get("tags") or []
                    print(f"分块内容: {chunk[:50]}...")
                    print(f"LLM 生成的标签: {tags}")
                    # 约束：长度与标签
                    if not chunk:
                        continue
                    if len(chunk) > max_chunk_chars:
                        chunk = chunk[:max_chunk_chars]
                    if not isinstance(tags, list):
                        tags = []
                    # 不再过滤标签，允许LLM自行生成的任何标签
                    if not tags:
                        tags = tag_candidates[:1] if tag_candidates else ["通用"]
                    print(f"最终使用的标签: {tags}")
                    
                    md = {"source": source, "title": title, "ord": ord_idx, "split": "llm", "tags": tags}
                    results.append(Document(page_content=chunk, metadata=md))
                    ord_idx += 1
            except Exception as e:
                print(f"[ERROR] LLM 调用失败: {e}")
                # LLM 调用失败时使用简单字符分块作为回退
                fallback_chunks = _fallback_chunking_for_window(w, max_chunk_chars, source, title, tag_candidates, ord_idx)
                results.extend(fallback_chunks)
                ord_idx += len(fallback_chunks)
    except Exception as e:
        print(f"[ERROR] LLM 分块过程发生错误: {e}")
        # 整体过程失败时使用简单字符分块作为回退
        return _fallback_chunking(text, max_chunk_chars, source, title, tag_candidates)
    
    # 如果最终没有得到任何分块，也使用回退策略
    if not results:
        print("[WARN] 没有得到任何有效的分块，使用回退策略")
        return _fallback_chunking(text, max_chunk_chars, source, title, tag_candidates)
    
    print("llm_chunk_and_tag结束")        
    print(f"llm_chunk_and_tag结果: {len(results)} 个分块")
    return results


def _fallback_chunking(text: str, max_chunk_chars: int, source: str, title: str, tag_candidates: List[str]) -> List[Document]:
    """简单的字符分块作为回退策略"""
    chunks = []
    current_chunk = ""
    
    # 按句子或段落进行简单分割
    sentences = []
    for para in text.split("\n\n"):
        if para.strip():
            # 简单按句号分割句子
            para_sentences = para.split("。")
            if para_sentences:
                sentences.extend([s + "。" for s in para_sentences[:-1]] + para_sentences[-1:])
    
    # 组合句子形成分块
    ord_idx = 0
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chunk_chars:
            if current_chunk.strip():
                # 添加当前分块
                tags = tag_candidates[:1] if tag_candidates else ["通用"]
                md = {"source": source, "title": title, "ord": ord_idx, "split": "fallback", "tags": tags}
                chunks.append(Document(page_content=current_chunk.strip(), metadata=md))
                ord_idx += 1
                current_chunk = sentence
            else:
                # 如果单个句子就超过最大长度，直接截断
                tags = tag_candidates[:1] if tag_candidates else ["通用"]
                md = {"source": source, "title": title, "ord": ord_idx, "split": "fallback", "tags": tags}
                chunks.append(Document(page_content=sentence[:max_chunk_chars], metadata=md))
                ord_idx += 1
        else:
            current_chunk += sentence
    
    # 添加最后一个分块
    if current_chunk.strip():
        tags = tag_candidates[:1] if tag_candidates else ["通用"]
        md = {"source": source, "title": title, "ord": ord_idx, "split": "fallback", "tags": tags}
        chunks.append(Document(page_content=current_chunk.strip(), metadata=md))
    
    print(f"[FALLBACK] 使用简单字符分块得到 {len(chunks)} 个分块")
    return chunks


def _fallback_chunking_for_window(text: str, max_chunk_chars: int, source: str, title: str, tag_candidates: List[str], start_ord: int) -> List[Document]:
    """对单个窗口使用简单字符分块作为回退策略"""
    chunks = _fallback_chunking(text, max_chunk_chars, source, title, tag_candidates)
    
    # 调整 ord 索引以保持连续性
    for i, chunk in enumerate(chunks):
        chunk.metadata["ord"] = start_ord + i
        chunk.metadata["split"] = "fallback_window"
    
    return chunks