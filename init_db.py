# -*- coding: utf-8 -*-
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

DDL = r"""
DROP TABLE IF EXISTS chunks;
DROP TABLE IF EXISTS documents;

CREATE TABLE documents (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  path         VARCHAR(512) NOT NULL UNIQUE,
  title        VARCHAR(512) NOT NULL,
  source_type  VARCHAR(64)  NULL,
  tags         JSON         NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chunks (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  doc_id        BIGINT      NOT NULL,
  ord           INT         NOT NULL,
  content       MEDIUMTEXT  NOT NULL,
  content_hash  CHAR(64)    NOT NULL UNIQUE,
  split         VARCHAR(16) NOT NULL,
  metadata      JSON        NULL,
  chunk_tags    JSON        NULL,
  created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_chunks_docs FOREIGN KEY (doc_id) REFERENCES documents(id)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_chunks_doc_ord     ON chunks(doc_id, ord);
CREATE FULLTEXT INDEX ft_chunks_txt ON chunks(content);

ALTER TABLE chunks
  ADD COLUMN tag0 VARCHAR(64) GENERATED ALWAYS AS (JSON_UNQUOTE(JSON_EXTRACT(chunk_tags,'$[0]'))) STORED,
  ADD INDEX idx_chunks_tag0 (tag0);
"""

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

if __name__ == "__main__":
    eng = build_engine()
    with eng.begin() as conn:
        for stmt in filter(None, DDL.split(";")):
            s = stmt.strip()
            if s:
                conn.execute(text(s))
    print("[OK] 数据库结构已重建")
