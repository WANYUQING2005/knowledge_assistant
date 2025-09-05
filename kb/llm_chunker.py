import os, json
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
     "   - 每个分块**必须**生成至少 1 个标签（通常为 1-2 个）。\n" 
     "   - **标签是必须项**，不允许输出没有标签的分块。\n"
     "   - **请生成大类标签**，例如：分块内容关于 TCP/UDP，应标记为“计算机网络”；分块内容关于 PyTorch，应标记为“机器学习”。\n"
     "   - 标签需体现该分块的**所属领域或学科类别**，而不是具体的技术细节或名词。\n"
     "   - 标签应简洁（1–4 个字/词），且具有较强的概括性和普适性。\n"
     "   - 分块内部语义保持一致，确保整体内容能被所选大类标签统一覆盖。\n"
     "   - 标签优先选择上位类别（学科/技术领域），如有必要才细分为二级类别。\n"
     "   - 即使难以归类的内容，也必须创建至少一个最接近的标签。\n"
     "\n"
     "3. 其他要求：\n"
     "   - 分块与标签之间必须一一对应。\n"
     "   - 即使内容模糊，也要尽量生成最接近的标签。\n"
     "   - 标签字段不能为空数组，必须包含至少一个有意义的标签。\n"
     "   - 输出格式：{schema}"),
    ("human",
     "以下仅供参考的标签例子（你可以创建完全不同的标签）：\n{tag_list}\n\nMAX_LEN={max_len}\n\n原始文本：\n{window_text}\n\n请直接给出 JSON 数组结果，确保每个分块都有标签。")
])


def _build_llm():
    return ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.1,
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
    return ["定义", "背景", "原理", "步骤", "参数", "示例", "注意事项", "限制", "性能", "对比", "引用", "FAQ"]


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

    llm = _build_llm()
    windows = _windows(text, int(os.getenv("LLM_CHUNK_WINDOW", _DEF_WIN)))

    results: List[Document] = []
    ord_idx = 0
    tag_list = "\n".join(f"- {t}" for t in tag_candidates)

    for w in windows:
        messages = PROMPT.format_messages(tag_list=tag_list, max_len=max_chunk_chars, window_text=w,schema=_SCHEMA)
        resp = llm.invoke(messages)
        content = resp.content if hasattr(resp, "content") else str(resp)
        data = _safe_parse(content)
        for item in data:
            chunk = (item.get("chunk") or "").strip()
            tags = item.get("tags") or []
            # 约束：长度与标签
            if not chunk:
                continue
            if len(chunk) > max_chunk_chars:
                chunk = chunk[:max_chunk_chars]
            # 确保tags是有效列表
            if not isinstance(tags, list):
                tags = []
            # 处理标签为空的极端情况，使用兜底标签
            if not tags:
                tags = tag_candidates[:1] if tag_candidates else ["通用"]

            # 标签规范化：去除空白、去重
            tags = [t.strip() for t in tags if t and isinstance(t, str)]
            tags = list(dict.fromkeys(tags))  # 去重保持顺序

            # 构建文档元数据
            md = {"source": source, "title": title, "ord": ord_idx, "split": "llm", "tags": tags}
            results.append(Document(page_content=chunk, metadata=md))
            ord_idx += 1

    return results
