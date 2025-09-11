# -*- coding: utf-8 -*-
"""
tag_search.py
基于“标签”的智能搜索（兼容多 OpenAI 风格接口）：
现在数据库里 title 就是标签。
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

def _build_llm():
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
        password=os.getenv("MYSQL_PASSWORD", "yourpassword"),
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

    # ✅ 现在直接用 title 字段作为标签
    def get_all_tags(self) -> Set[str]:
        tags: Set[str] = set()
        sql = text("SELECT DISTINCT title FROM knowledge_ragchunks WHERE title IS NOT NULL AND title != ''")
        with self.engine.begin() as conn:
            for row in conn.execute(sql):
                if row.title and row.title.strip():
                    tags.add(row.title.strip())
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
        hits = [t for t in all_tags if q in t.lower() or t.lower() in q]
        seen, result = set(), []
        for t in hits:
            if t not in seen:
                seen.add(t)
                result.append(t)
            if len(result) >= topk:
                break
        return result

    # ✅ 根据 title 取 chunks
    def get_chunks_by_tags(self, tags: List[str], limit_per_tag: int = 50) -> List[Dict[str, Any]]:
        if not tags:
            return []

        conds, params = [], {}
        for i, t in enumerate(tags):
            pn = f"tag_{i}"
            conds.append(f"title = :{pn}")
            params[pn] = t
        where_clause = " OR ".join(conds)

        sql = text(f"""
            SELECT
                id, title, content, vector_id, number, word_count,
                document_id, creater_id, create_at, `kb id`
            FROM knowledge_ragchunks
            WHERE {where_clause}
            ORDER BY document_id ASC, number ASC
            LIMIT :lim
        """)
        params["lim"] = limit_per_tag * max(1, len(tags))

        out: List[Dict[str, Any]] = []
        with self.engine.begin() as conn:
            for row in conn.execute(sql, params):
                out.append({
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "vector_id": row.vector_id,
                    "number": row.number,
                    "word_count": row.word_count,
                    "document_id": row.document_id,
                    "creater_id": row.creater_id,
                    "create_at": str(row.create_at),
                    "kb_id": getattr(row, "kb id", None)
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
                    print(f"🛣  源: {ch.get('source', '-')}")
                    print(f"🧭 向量ID: {ch.get('vector_id')}")
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
