# -*- coding: utf-8 -*-
"""
tag_search.py
基于“标签”的智能搜索（兼容多 OpenAI 风格接口）：
1) 汇总 DB 中所有标签（metadata.tags 与 chunk_tags）
2) 用 LLM（ChatOpenAI + 可配置 API_BASE / API_KEY / MODEL）做语义匹配
3) 回退到字符串包含匹配（兜底）
4) 返回匹配标签与相关 chunks（含 faiss_id/文档标题/路径/预览）
"""

import os
import json
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from langchain_openai import ChatOpenAI

load_dotenv()


# ------------------ LLM ------------------

def     _build_llm():
    """
    兼容多 OpenAI 风格接口（含 DeepSeek、One-API、OpenRouter、自建代理等）
    环境变量优先级：
    - API_KEY:      密钥
    - API_BASE:     接口根路径（如 https://api.deepseek.com 或你的网关地址）
    - MODEL:        模型名（如 deepseek-chat / gpt-4o-mini / qwen-max 等）
    """
    return ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.1,
    )


# ------------------ DB ------------------

def _build_engine():
    url_env = os.getenv("MYSQL_URL")
    if url_env:
        return create_engine(url_env, pool_pre_ping=True)

    url_obj = URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "wyq20050725"),
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        database=os.getenv("MYSQL_DB", "knowledge_assistant"),
    )
    return create_engine(url_obj, pool_pre_ping=True)


# ------------------ 核心类 ------------------

class TagBasedSearch:
    """基于标签的搜索：收集标签 → LLM 匹配 → 取回相关 chunks"""

    def __init__(self):
        self.engine = _build_engine()
        self.llm = _build_llm()

    # 统一收集 metadata.tags + chunk_tags
    def get_all_tags(self) -> Set[str]:
        tags: Set[str] = set()
        sql = text("""
            SELECT metadata, chunk_tags
            FROM knowledge_ragchunks
            WHERE (metadata IS NOT NULL) OR (chunk_tags IS NOT NULL)
        """)
        with self.engine.begin() as conn:
            for row in conn.execute(sql):
                # metadata.tags
                if row.metadata:
                    try:
                        md = json.loads(row.metadata)
                        ts = md.get("tags", [])
                        if isinstance(ts, list):
                            for t in ts:
                                if isinstance(t, str) and t.strip():
                                    tags.add(t.strip())
                    except Exception:
                        pass
                # chunk_tags（独立 JSON 列）
                if row.chunk_tags:
                    try:
                        ct = json.loads(row.chunk_tags)
                        if isinstance(ct, list):
                            for t in ct:
                                if isinstance(t, str) and t.strip():
                                    tags.add(t.strip())
                    except Exception:
                        pass
        return tags

    def _llm_match(self, query: str, all_tags: Set[str], topk: int = 10) -> List[str]:
        """用 LLM 从标签集中筛选最相关标签；失败回退到字符串匹配"""
        if not all_tags:
            return []

        tags_str = "\n".join(f"- {t}" for t in sorted(all_tags))
        prompt = f"""
你是一个精确的标签匹配专家。请根据用户的搜索查询，从给定的标签列表中严格筛选最相关的标签。

用户搜索查询: "{query}"

可用标签列表:
{tags_str}

请严格遵循：
1) 仅选择与查询高度相关的标签（宁缺毋滥）
2) 同义词/专业等价表达可视为相关
3) 按相关度从高到低排序
4) 输出格式：每行一个标签，不要额外说明
"""

        try:
            # ChatOpenAI: 直接传 messages 或字符串均可；这里用 messages 方式更稳妥
            resp = self.llm.invoke([{"role": "user", "content": prompt}])
            text_out = resp.content if hasattr(resp, "content") else (resp or "")
            matched: List[str] = []
            for line in text_out.strip().splitlines():
                tag = line.strip().lstrip("-").strip()
                if tag and (tag in all_tags) and (tag not in matched):
                    matched.append(tag)
            return matched[:topk] if matched else self._fallback_match(query, all_tags, topk)
        except Exception as e:
            print(f"[WARN] LLM 匹配失败，回退到字符串匹配: {e}")
            return self._fallback_match(query, all_tags, topk)

    def _fallback_match(self, query: str, all_tags: Set[str], topk: int = 10) -> List[str]:
        q = query.lower().strip()
        hits = []
        for t in all_tags:
            tl = t.lower()
            if q in tl or tl in q:
                hits.append(t)
        # 去重保序（按标签字母序也可，这里保留发现顺序）
        seen = set()
        result = []
        for t in hits:
            if t not in seen:
                seen.add(t)
                result.append(t)
            if len(result) >= topk:
                break
        return result

    def get_chunks_by_tags(self, tags: List[str], limit_per_tag: int = 50) -> List[Dict[str, Any]]:
        """根据匹配标签取回关联 chunks（按 doc_id / ord 排序）"""
        if not tags:
            return []

        conds = []
        params = {}
        for i, t in enumerate(tags):
            pn = f"tag_{i}"
            conds.append(
                f"(JSON_CONTAINS(metadata, JSON_QUOTE(:{pn}), '$.tags') "
                f" OR JSON_CONTAINS(chunk_tags, JSON_QUOTE(:{pn})))"
            )
            params[pn] = t
        where_clause = " OR ".join(conds)

        sql = text(f"""
            SELECT
                c.content_hash, c.content, c.metadata, c.ord, c.doc_id, c.split, c.faiss_id, c.chunk_tags,
                d.title, d.path AS source
            FROM knowledge_ragchunks c
            JOIN knowledge_ragdocuments d ON c.doc_id = d.id
            WHERE {where_clause}
            ORDER BY c.doc_id ASC, c.ord ASC
            LIMIT :lim
        """)
        params["lim"] = limit_per_tag * max(1, len(tags))

        out: List[Dict[str, Any]] = []
        with self.engine.begin() as conn:
            for row in conn.execute(sql, params):
                try:
                    md = json.loads(row.metadata) if row.metadata else {}
                except Exception:
                    md = {}
                try:
                    ct = json.loads(row.chunk_tags) if row.chunk_tags else []
                except Exception:
                    ct = []
                out.append({
                    "content_hash": row.content_hash,
                    "content": row.content,
                    "ord": row.ord,
                    "doc_id": row.doc_id,
                    "title": row.title,
                    "source": row.source,
                    "split": row.split,
                    "faiss_id": row.faiss_id,
                    "tags": (md.get("tags") or ct) or []
                })
        return out

    def search_by_tags(self, query: str, topk_tags: int = 8, limit_per_tag: int = 50) -> Dict[str, Any]:
        print(f"🔎 基于标签搜索：{query}")
        all_tags = self.get_all_tags()
        print(f"[INFO] 标签总数：{len(all_tags)}")
        if not all_tags:
            return {"query": query, "matched_tags": [], "chunks": [], "message": "数据库中没有任何标签"}

        matched = self._llm_match(query, all_tags, topk=topk_tags)
        print(f"[INFO] 匹配标签：{matched}")
        if not matched:
            return {"query": query, "matched_tags": [], "chunks": [], "message": "未匹配到相关标签"}

        chunks = self.get_chunks_by_tags(matched, limit_per_tag=limit_per_tag)
        print(f"[INFO] 命中知识块：{len(chunks)}")
        return {
            "query": query,
            "matched_tags": matched,
            "chunks": chunks,
            "message": f"命中 {len(chunks)} 个知识块"
        }


# ------------------ CLI ------------------

def main():
    searcher = TagBasedSearch()
    print("=" * 60)
    print("🏷️  基于标签的智能搜索（兼容多 OpenAI 接口）")
    print("=" * 60)
    print("输入搜索词并回车；输入 exit 退出。\n")

    while True:
        try:
            q = input("🔍 请输入搜索词: ").strip()
            if not q:
                continue
            if q.lower() == "exit":
                print("👋 再见！")
                break

            result = searcher.search_by_tags(q)

            print("\n" + "=" * 50)
            print("🎯 搜索结果")
            print("=" * 50)

            # 标签
            tags = result.get("matched_tags") or []
            print("📌 匹配的标签：", ", ".join(tags) if tags else "无")

            # 知识块
            chs = result.get("chunks") or []
            if chs:
                print(f"\n📚 相关知识块（展示前 5 条，共 {len(chs)} 条）\n")
                for i, ch in enumerate(chs[:5], 1):
                    preview = (ch["content"][:200] + "...") if len(ch["content"]) > 200 else ch["content"]
                    print(f"--- 知识块 {i} ---")
                    print(f"📄 文档: {ch['title']}")
                    print(f"🛣  源: {ch['source']}")
                    print(f"🏷  标签: {', '.join(ch.get('tags', []))}")
                    print(f"🧭 faiss_id: {ch.get('faiss_id')}")
                    print(f"📝 内容: {preview}\n")
                if len(chs) > 5:
                    print(f"... 还有 {len(chs) - 5} 条")
            else:
                print("❌ 未找到相关知识块")

            print("💡", result.get("message", ""))

            print("\n" + "=" * 50 + "\n")
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 出错：{e}")


if __name__ == "__main__":
    main()
