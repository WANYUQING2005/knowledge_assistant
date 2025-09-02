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

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 智谱API一次可批量输入；SDK为OpenAI风格
        resp = self.client.embeddings.create(model=self.model, input=texts)
        # 返回与输入对应的 embedding 列表
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> List[float]:
        return self.embed_documents([text])[0]
