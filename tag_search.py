# -*- coding: utf-8 -*-
"""
基于标签的智能搜索功能
通过大模型匹配用户搜索词与数据库标签，返回相关chunks
"""
import os
import json
import requests
from typing import List, Dict, Any, Set
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from langchain_openai import ChatOpenAI

load_dotenv()

class DeepSeekLLM:
    """DeepSeek API 封装"""
    def __init__(self, api_key: str, model: str = "deepseek-chat", temperature: float = 0.1):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

    def _call(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": 512
        }
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

class TagBasedSearch:
    """基于标签的智能搜索类"""

    def __init__(self):
        self.engine = self._build_engine()
        self.llm = self._build_llm()

    def _build_engine(self):
        """构建数据库连接"""
        url_env = os.getenv("MYSQL_URL")
        if url_env:
            return create_engine(url_env, pool_pre_ping=True)
        url_obj = URL.create(
            "mysql+pymysql",
            username=os.getenv("MYSQL_USER", "rag"),
            password=os.getenv("MYSQL_PASSWORD", "yourpassword"),
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DB", "rag_demo"),
        )
        return create_engine(url_obj, pool_pre_ping=True)

    def _build_llm(self):
        """构建DeepSeek LLM实例"""
        return ChatOpenAI(
        api_key=os.getenv("API_KEY"),
        base_url=os.getenv("API_BASE", "https://api.deepseek.com"),
        model=os.getenv("MODEL", "deepseek-chat"),
        temperature=0.1,
    )

    def get_all_tags(self) -> Set[str]:
        """从数据库中提取所有唯一标签"""
        all_tags = set()

        query = text("""
            SELECT metadata FROM chunks 
            WHERE metadata IS NOT NULL 
            AND JSON_EXTRACT(metadata, '$.tags') IS NOT NULL
        """)

        with self.engine.begin() as conn:
            result = conn.execute(query)
            for row in result:
                try:
                    metadata = json.loads(row.metadata)
                    tags = metadata.get('tags', [])
                    if isinstance(tags, list):
                        all_tags.update(tags)
                except (json.JSONDecodeError, TypeError):
                    continue

        return all_tags

    def match_tags_with_llm(self, search_query: str, all_tags: Set[str]) -> List[str]:
        """使用大模型匹配搜索词与标签"""
        if not all_tags:
            return []

        tags_list = list(all_tags)
        tags_str = "\n".join(f"- {tag}" for tag in tags_list)

        prompt = f"""
你是一个精确的标签匹配专家。请根据用户的搜索查询，从给定的标签列表中严格筛选最相关的标签。

用户搜索查询: "{search_query}"

可用标签列表:
{tags_str}

请严格按照以下标准进行匹配:
1. 仅选择与搜索查询高度相关的标签，忽略模糊相关的标签
2. 优先考虑直接匹配的关键词和核心概念
3. 考虑同义词和专业术语的等价关系
4. 按相关度从高到低排序，只返回真正相关的标签
5. 宁缺毋滥，如果没有高度相关的标签，可以少返回甚至不返回

请直接返回匹配的标签列表，每行一个标签，不要添加任何其他解释:
"""

        try:
            response = self.llm._call(prompt)
            # 解析返回的标签
            matched_tags = []
            for line in response.strip().split('\n'):
                tag = line.strip().lstrip('-').strip()
                if tag and tag in all_tags:
                    matched_tags.append(tag)

            return matched_tags[:10]  # 最多返回10个标签

        except Exception as e:
            print(f"LLM标签匹配失败: {e}")
            # 回退到简单的字符串匹配
            return self._fallback_tag_matching(search_query, all_tags)

    def _fallback_tag_matching(self, search_query: str, all_tags: Set[str]) -> List[str]:
        """回退的标签匹配方法（基于字符串相似度）"""
        search_lower = search_query.lower()
        matched_tags = []

        for tag in all_tags:
            tag_lower = tag.lower()
            if search_lower in tag_lower or tag_lower in search_lower:
                matched_tags.append(tag)

        return matched_tags[:10]

    def get_chunks_by_tags(self, tags: List[str]) -> List[Dict[str, Any]]:
        """根据标签获取相关的chunks"""
        if not tags:
            return []

        # 构建查询条件
        tag_conditions = []
        params = {}

        for i, tag in enumerate(tags):
            param_name = f"tag_{i}"
            tag_conditions.append(f"JSON_CONTAINS(metadata, JSON_QUOTE(:{param_name}), '$.tags')")
            params[param_name] = tag

        # 使用OR连接所有标签条件
        where_clause = " OR ".join(tag_conditions)

        query = text(f"""
            SELECT 
                c.content_hash,
                c.content,
                c.metadata,
                c.ord,
                c.doc_id,
                d.title,
                d.path as source
            FROM chunks c
            JOIN documents d ON c.doc_id = d.id
            WHERE {where_clause}
            ORDER BY c.doc_id, c.ord
        """)

        chunks = []
        with self.engine.begin() as conn:
            result = conn.execute(query, params)
            for row in result:
                try:
                    metadata = json.loads(row.metadata) if row.metadata else {}
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

                chunk_data = {
                    "content_hash": row.content_hash,
                    "content": row.content,
                    "metadata": metadata,
                    "ord": row.ord,
                    "doc_id": row.doc_id,
                    "title": row.title,
                    "source": row.source,
                    "tags": metadata.get("tags", [])
                }
                chunks.append(chunk_data)

        return chunks

    def search_by_tags(self, search_query: str) -> Dict[str, Any]:
        """完整的基于标签的搜索流程"""
        print(f"🔍 开始基于标签的搜索: {search_query}")

        # 1. 获取所有标签
        print("📋 正在从数据库获取所有标签...")
        all_tags = self.get_all_tags()
        print(f"📊 找到 {len(all_tags)} 个唯一标签")

        if not all_tags:
            return {
                "query": search_query,
                "matched_tags": [],
                "chunks": [],
                "message": "数据库中没有找到任何标签"
            }

        # 2. 使用大模型匹配标签
        print("🤖 正在使用AI匹配相关标签...")
        matched_tags = self.match_tags_with_llm(search_query, all_tags)
        print(f"✅ 匹配到 {len(matched_tags)} 个相关标签: {matched_tags}")

        if not matched_tags:
            return {
                "query": search_query,
                "matched_tags": [],
                "chunks": [],
                "message": "未找到与搜索词相关的标签"
            }

        # 3. 根据匹配的标签获取chunks
        print("📚 正在获取相关的知识块...")
        chunks = self.get_chunks_by_tags(matched_tags)
        print(f"📖 找到 {len(chunks)} 个相关的知识块")

        return {
            "query": search_query,
            "matched_tags": matched_tags,
            "chunks": chunks,
            "message": f"成功找到 {len(chunks)} 个相关知识块"
        }


def tag_search():
    """主函数 - 交互式标签搜索"""
    searcher = TagBasedSearch()

    print("="*60)
    print("🏷️  基于标签的智能搜索系统")
    print("="*60)
    print("输入搜索词，系统将通过AI匹配相关标签并返回知识块")
    print("输入 'exit' 退出程序")
    print()

    while True:
        try:
            query = input("🔍 请输入搜索词: ").strip()

            if not query:
                continue

            if query.lower() == 'exit':
                print("👋 再见！")
                break

            # 执行搜索
            result = searcher.search_by_tags(query)

            print("\n" + "="*50)
            print("🎯 搜索结果")
            print("="*50)

            # 显示匹配的标签
            if result["matched_tags"]:
                print(f"📌 匹配的标签 ({len(result['matched_tags'])}个):")
                for i, tag in enumerate(result["matched_tags"], 1):
                    print(f"   {i}. {tag}")
                print()

            # 显示找到的chunks
            if result["chunks"]:
                print(f"📚 相关知识块 ({len(result['chunks'])}个):")
                print()

                for i, chunk in enumerate(result["chunks"][:5], 1):  # 最多显示前5个
                    print(f"--- 知识块 {i} ---")
                    print(f"📄 文档: {chunk['title']}")
                    print(f"🏷️  标签: {', '.join(chunk['tags'])}")
                    print(f"📝 内容: {chunk['content'][:200]}...")
                    print()

                if len(result["chunks"]) > 5:
                    print(f"... 还有 {len(result['chunks']) - 5} 个知识块")
            else:
                print("❌ 未找到相关的知识块")

            print("💡", result["message"])
            print("\n" + "="*50 + "\n")

        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 搜索过程中出错: {e}")


if __name__ == "__main__":
    tag_search()

