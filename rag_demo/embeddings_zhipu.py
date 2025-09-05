# -*- coding: utf-8 -*-
import os
from typing import List
from zhipuai import ZhipuAI
from langchain_core.embeddings import Embeddings

class ZhipuAIEmbeddingsLC(Embeddings):
    """
    LangChain Embeddings 适配：调用智谱AI的 embedding 接口。
    """
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        self.model = model or os.getenv("ZHIPUAI_EMBED_MODEL", "embedding-2")
        if not self.api_key:
            raise ValueError("缺少 ZHIPUAI_API_KEY")
        self.client = ZhipuAI(api_key=self.api_key)
        # 智谱AI API每批次的最大文本数量
        self.batch_size = 64

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 分批处理，每批次最多batch_size条文本
        results = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            # 智谱API批量调用；SDK为OpenAI风格
            resp = self.client.embeddings.create(model=self.model, input=batch_texts)
            # 将每批次的结果添加到总结果中
            results.extend([item.embedding for item in resp.data])
        return results

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
