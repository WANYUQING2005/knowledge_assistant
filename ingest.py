# ingest.py（支持 LLM 分块 + 标签 + Q&A/字符回退）
# -*- coding: utf-8 -*-
"""
在原版基础上，增加：
1) **LLM 分块并打标签**：优先使用大模型对整文进行语义分块；每块从预设标签集中选择 1-3 个标签写入 metadata.tags。
2) **最大长度限制**：通过环境变量 MAX_CHUNK_CHARS 控制每个分块最大字符数（默认 400）。
3) **回退策略**：若 LLM 分块失败或返回为空，依次回退到 Q&A 切分（qa）→ 字符切分（char）。
4) 其余逻辑（MySQL 去重入库、FAISS 增量更新）保持不变。

"""
import os, glob, json, hashlib, re
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from embeddings_zhipu import ZhipuAIEmbeddingsLC
from loaders import load_any
from llm_chunker import llm_chunk_and_tag, load_tag_candidates

load_dotenv()


def build_engine():
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

engine = build_engine()



def sha256(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Q&A 正则
_QA_REGEX = re.compile(
    r"(?:^|\n+)\s*(?:Q|Question|问|问题)\s*[:：\]]?\s*(.+?)\s*"
    r"(?:\n+|\r+)\s*(?:A|Answer|答|答案)\s*[:：\]]?\s*(.+?)"
    r"(?=(?:\n+\s*(?:Q|Question|问|问题)\s*[:：\]]?)|\Z)",
    re.S | re.I
)




def qa_splitter(text: str, source: str, title: str):
    docs = []
    i = 0
    for m in _QA_REGEX.finditer(text):
        q = m.group(1).strip()
        a = m.group(2).strip()
        if not q or not a:
            continue
        content = f"Q: {q}\nA: {a}"
        metadata = {"source": source, "title": title, "ord": i, "split": "qa"}
        docs.append(Document(page_content=content, metadata=metadata))
        i += 1
    return docs

# ------------------------- DB 写入 -------------------------

def upsert_document(path,title,source_type="file",tags=None):
    with engine.begin() as conn:
        r = conn.execute(text("SELECT id FROM documents WHERE path=:p"),{"p":path}).fetchone()
        if r:
            conn.execute(text("UPDATE documents SET source_type=:st, tags=:tg WHERE id=:id"),
                         {"st":source_type, "tg": json.dumps(tags) if tags else None, "id": r[0]})
            return r[0]
        res = conn.execute(
            text("""INSERT INTO documents(path,title,source_type,tags)
                    VALUES(:p,:t,:st,:tg)"""),
            {"p":path,"t":title,"st":source_type,"tg": json.dumps(tags) if tags else None}
        )
        return res.lastrowid


def insert_chunk_if_new(doc_id, ord_idx, content, metadata):

    h = sha256(content.strip())
    split = (metadata or {}).get("split", "char")
    chunk_tags = (metadata or {}).get("tags", [])

    with engine.begin() as conn:
        r = conn.execute(text("SELECT id FROM chunks WHERE content_hash=:h"), {"h": h}).fetchone()
        if r:
            return None
        conn.execute(
            text("""
                INSERT INTO chunks(doc_id, ord, content, metadata, content_hash, split, chunk_tags)
                VALUES(:doc_id, :ord, :content, :metadata, :h, :split, :chunk_tags)
            """),
            {
                "doc_id": doc_id,
                "ord": ord_idx,
                "content": content,
                "metadata": json.dumps(metadata, ensure_ascii=False) if metadata else None,
                "h": h,
                "split": split,
                "chunk_tags": json.dumps(chunk_tags, ensure_ascii=False) if chunk_tags else None,
            }
        )
    return h


# ------------------------- 主流程 -------------------------

def main():
    files = []
    for pat in ["data/*.txt","data/*.md","data/*.pdf","data/*.docx"]:
        files.extend(glob.glob(pat))
    if not files:
        print("data/ 目录为空，请放入 txt/md/pdf/docx 文件")
        return

    # 参数：最大分块长度
    max_len = int(os.getenv("MAX_CHUNK_CHARS", "400"))

    # 回退用字符切分器
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_len, chunk_overlap=max(0, max_len//2),
        separators=["\n\n","\n","。","！","？","，"," ", ""]
    )

    # 预设标签集合
    tag_candidates = load_tag_candidates()

    embeddings = ZhipuAIEmbeddingsLC()

    index_dir = "index/faiss"
    if os.path.isdir(index_dir):
        vs = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
        print("[INFO] 已加载现有 FAISS 索引，增量更新中...")
    else:
        vs = None
        os.makedirs("index", exist_ok=True)

    new_docs_for_vs = []

    for path in files:
        raw_docs = load_any(path)
        if not raw_docs:
            print(f"[SKIP] 不支持的类型或空文档: {path}")
            continue

        title = os.path.basename(path)
        source_type = raw_docs[0].metadata.get("source_type","file")
        doc_id = upsert_document(path, title, source_type=source_type, tags=None)

        merged_text = "\n\n".join([d.page_content for d in raw_docs])

        # 1) 优先：LLM 分块 + 标签
        llm_docs = llm_chunk_and_tag(merged_text, tag_candidates, max_chunk_chars=max_len,
                                      source=path, title=title)
        if llm_docs:
            chunks_docs = llm_docs
            mode = "llm"
            print(f"[MODE] LLM 分块 → {len(chunks_docs)}：{title}")
        else:
            # 2) 回退：Q&A
            qa_docs = qa_splitter(merged_text, path, title)
            if qa_docs:
                chunks_docs = qa_docs
                mode = "qa"
                print(f"[MODE] Q&A 切分 → {len(chunks_docs)}：{title}")
            else:
                # 3) 回退：字符
                chunks_texts = char_splitter.split_text(merged_text)
                chunks_docs = [
                    Document(
                        page_content=ch,
                        metadata={"source": path, "title": title, "ord": i, "split": "char", "tags": []}
                    )
                    for i, ch in enumerate(chunks_texts)
                ]
                mode = "char"
                print(f"[MODE] 字符切分 → {len(chunks_docs)}：{title}")

        cnt_new = 0
        for i, doc in enumerate(chunks_docs):
            doc.metadata.setdefault("ord", i)
            doc.metadata.setdefault("source", path)
            doc.metadata.setdefault("title", title)
            doc.metadata.setdefault("split", mode)
            doc.metadata.setdefault("tags", doc.metadata.get("tags", []))

            # 兜底：长度裁剪
            if len(doc.page_content) > max_len:
                doc.page_content = doc.page_content[:max_len]

            h = insert_chunk_if_new(doc_id, i, doc.page_content, doc.metadata)
            if h:
                new_docs_for_vs.append(doc)
                cnt_new += 1

        print(f"[OK] {title}：入库片段 {len(chunks_docs)}，其中新增 {cnt_new}")

    if not new_docs_for_vs:
        print("[INFO] 无新增切片，索引不变。")
        return

    if vs is None:
        vs = FAISS.from_documents(new_docs_for_vs, embeddings)
    else:
        vs.add_documents(new_docs_for_vs)

    vs.save_local(index_dir)
    print(f"[OK] 索引已保存：{index_dir}，本次新增向量 {len(new_docs_for_vs)}")

if __name__ == "__main__":
    main()

