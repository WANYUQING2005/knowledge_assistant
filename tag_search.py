

import os
import json
import argparse
import csv
from typing import List, Dict, Any, Set, Tuple
from dotenv import load_dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# ------------------------- 连接配置 -------------------------

def build_engine():
    """
    逻辑与 ingest.py 中一致：优先读取 MYSQL_URL；否则拼接单项配置。
    """
    url_env = os.getenv("MYSQL_URL")
    if url_env:
        return create_engine(url_env, pool_pre_ping=True)

    url_obj = URL.create(
        "mysql+pymysql",
        username=os.getenv("MYSQL_USER","rag"),
        password=os.getenv("MYSQL_PASSWORD","yourpassword"),
        host=os.getenv("MYSQL_HOST","127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT","3306")),
        database=os.getenv("MYSQL_DB","rag_demo"),
    )
    return create_engine(url_obj, pool_pre_ping=True)

# ------------------------- 实用函数 -------------------------

def _norm_tag(t: str) -> str:
    return (t or "").strip().replace("　"," ").replace("\u3000"," ").lower()

def _parse_chunk_tags(s: str) -> List[str]:
    """
    将表中的 chunk_tags 文本解析为 list[str]；
    容错：若不是合法 JSON，则尝试用逗号/空格切分。
    """
    if not s:
        return []
    try:
        data = json.loads(s)
        if isinstance(data, list):
            return [_norm_tag(x) for x in data if isinstance(x, str)]
    except Exception:
        pass
    # 回退：粗略分割
    parts = [p.strip() for p in s.replace("[","").replace("]","").replace('"','').split(",")]
    return [_norm_tag(p) for p in parts if p]

def _match_tags(candidate: List[str], query: List[str], mode: str) -> bool:
    """
    mode='any'：候选标签与查询标签有交集即可；
    mode='all'：候选标签至少包含所有查询标签；
    """
    cand = set(candidate)
    qset = set(query)
    if mode == "all":
        return qset.issubset(cand)
    return len(cand & qset) > 0

# ------------------------- 查询核心 -------------------------

def find_chunks_by_tags(tags: List[str], mode: str = "any", limit: int = 2000) -> List[Dict[str, Any]]:
    """
    返回匹配到的分块记录列表：
      id, doc_id, ord, split, snippet, tags(list), title, source(path)
    """
    engine = build_engine()
    q = text("""
        SELECT c.id, c.doc_id, c.ord, c.split, c.content, c.chunk_tags,
               d.title, d.path AS source
        FROM chunks c
        JOIN documents d ON c.doc_id = d.id
        ORDER BY c.id DESC
        """)
    out: List[Dict[str, Any]] = []
    with engine.begin() as conn:
        for row in conn.execute(q):
            row = dict(row._mapping)
            ctags = _parse_chunk_tags(row.get("chunk_tags"))
            if not ctags:
                continue
            if _match_tags(ctags, tags, mode):
                content = (row.get("content") or "").strip()
                snippet = content if len(content) <= 240 else content[:240] + "…"
                out.append({
                    "id": row["id"],
                    "doc_id": row["doc_id"],
                    "ord": row["ord"],
                    "split": row["split"],
                    "snippet": snippet,
                    "tags": ctags,
                    "title": row.get("title"),
                    "source": row.get("source"),
                })
                if len(out) >= limit:
                    break
    return out

def distinct_sources(results: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """
    提取去重后的 (title, source) 列表，按标题排序。
    """
    s: Set[Tuple[str,str]] = set()
    for r in results:
        s.add((r.get("title") or "", r.get("source") or ""))
    return sorted(list(s), key=lambda x: (x[0], x[1]))

# ------------------------- CLI -------------------------

def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="按标签查询分块（chunks）")
    ap.add_argument("--tags", nargs="+", required=True, help="要查询的标签（支持多个）")
    ap.add_argument("--mode", choices=["any","all"], default="any", help="any=包含任意一个标签；all=同时包含全部标签")
    ap.add_argument("--limit", type=int, default=2000, help="最多返回多少条分块")
    ap.add_argument("--list-docs", action="store_true", help="仅输出匹配到的来源文件列表（去重）")
    ap.add_argument("--csv", type=str, default="", help="将结果导出到 CSV 文件路径")
    args = ap.parse_args()



    qtags = [_norm_tag(t) for t in args.tags if _norm_tag(t)]
    if not qtags:
        print("无有效标签。")
        return

    results = find_chunks_by_tags(qtags, mode=args.mode, limit=args.limit)

    if args.list_docs:
        print(f"匹配标签 {qtags} 的来源文件（共 {len(distinct_sources(results))} 个）：\n")
        for title, source in distinct_sources(results):
            print(f"- {title}  ({source})")
        return

    print(f"匹配标签 {qtags} 的分块（共 {len(results)} 条）：\n")
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['title']}  ({r['source']})  ord={r['ord']} split={r['split']}  tags={r['tags']}")
        print(f"    {r['snippet']}\n")

    if args.csv:
        path = args.csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["id","doc_id","ord","split","title","source","tags","snippet"])
            for r in results:
                w.writerow([r["id"], r["doc_id"], r["ord"], r["split"], r["title"], r["source"], " ".join(r["tags"]), r["snippet"]])
        print(f"\n已导出 CSV：{path}")

if __name__ == "__main__":
    main()
