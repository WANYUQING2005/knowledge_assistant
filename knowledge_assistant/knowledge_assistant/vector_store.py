import faiss
import numpy as np

class FAISSVectorStore:
    def __init__(self, dimension=256):
        self.index = faiss.IndexFlatL2(dimension)
        self.ids = []  # 存储向量对应的ID
        self.dimension = dimension

    def add_vectors(self, vectors, ids):
        """添加向量到索引
        vectors: numpy数组，形状为(n, dimension)
        ids: 与向量对应的唯一标识符列表
        """
        # 首先检查输入有效性
        if len(vectors) != len(ids):
            raise ValueError("向量数量和ID数量不匹配")
        
        if vectors.shape[1] != self.dimension:
            raise ValueError(f"向量维度不匹配，期望维度: {self.dimension}, 实际维度: {vectors.shape[1]}")
        
        # 然后添加到索引
        self.index.add(np.array(vectors, dtype=np.float32))
        self.ids.extend(ids)

    def search_similar(self, query_vector, top_k=5):
        """搜索相似向量
        query_vector: 形状为(dimension,) 或 (1, dimension) 的numpy数组
        返回格式: [(id, distance), ...]
        """
        # 确保query_vector是二维数组
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # 确保维度匹配
        if query_vector.shape[1] != self.dimension:
            raise ValueError(f"查询向量维度不匹配，期望维度: {self.dimension}, 实际维度: {query_vector.shape[1]}")
        
        # 正确的搜索调用方式
        distances, indices = self.index.search(query_vector.astype(np.float32), top_k)
        
        results = []
        for j, i in enumerate(indices[0]):
            if i != -1 and i < len(self.ids):  # 确保索引有效
                # 显式转换为Python float
                results.append((self.ids[i], float(distances[0][j])))
        
        return results

    def save_index(self, path):
        """保存索引到磁盘"""
        faiss.write_index(self.index, path)

    def load_index(self, path):
        """从磁盘加载索引"""
        self.index = faiss.read_index(path)
