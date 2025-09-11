import unittest
import numpy as np
import faiss
import unittest
import tempfile
import os
import shutil
from pathlib import Path
import sys

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))
from knowledge_assistant.knowledge_assistant.vector_store import FAISSVectorStore

class TestFAISSVectorStore(unittest.TestCase):

    def setUp(self):
        """测试前的准备工作"""
        self.dimension = 256
        self.vector_store = FAISSVectorStore(dimension=self.dimension)
        
        # 创建测试数据
        self.test_vectors = np.random.rand(10, self.dimension).astype(np.float32)
        self.test_ids = [f"id_{i}" for i in range(10)]
        
        # 单个查询向量（一维）
        self.query_vector = np.random.rand(self.dimension).astype(np.float32)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.vector_store.ids), 0)
        self.assertEqual(self.vector_store.index.d, self.dimension)

    def test_add_vectors(self):
        """测试添加向量"""
        # 添加向量
        self.vector_store.add_vectors(self.test_vectors, self.test_ids)
        
        # 验证向量数量
        self.assertEqual(self.vector_store.index.ntotal, 10)
        self.assertEqual(len(self.vector_store.ids), 10)
        
        # 验证ID正确存储
        self.assertEqual(self.vector_store.ids, self.test_ids)

    def test_add_vectors_with_mismatched_dimension(self):
        """测试添加维度不匹配的向量"""
        wrong_dim_vectors = np.random.rand(5, 128).astype(np.float32)  # 错误的维度
        wrong_ids = [f"wrong_{i}" for i in range(5)]
        
        # 这里应该在我们的验证中抛出ValueError
        with self.assertRaises(ValueError):
            self.vector_store.add_vectors(wrong_dim_vectors, wrong_ids)

    def test_search_similar_empty_index(self):
        """测试在空索引中搜索"""
        results = self.vector_store.search_similar(self.query_vector)
        self.assertEqual(len(results), 0)

    def test_search_similar(self):
        """测试相似性搜索"""
        # 添加向量
        self.vector_store.add_vectors(self.test_vectors, self.test_ids)
        
        # 搜索
        results = self.vector_store.search_similar(self.query_vector, top_k=3)
        
        # 验证结果格式和数量
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIn(result[0], self.test_ids)
            # 现在返回的是Python float类型
            self.assertIsInstance(result[1], float)

    def test_search_similar_with_exact_match(self):
        """测试精确匹配搜索"""
        # 创建一个特殊的测试场景：添加查询向量本身
        exact_id = "exact_match"
        exact_vector = self.query_vector.reshape(1, -1)  # 转换为二维
        self.vector_store.add_vectors(exact_vector, [exact_id])
        
        # 搜索应该返回自身作为最相似的结果
        results = self.vector_store.search_similar(self.query_vector, top_k=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], exact_id)
        # 自身距离应该非常接近0（由于浮点精度可能不是精确的0）
        self.assertAlmostEqual(results[0][1], 0.0, places=6)

    def test_search_similar_top_k_larger_than_index(self):
        """测试请求的top_k大于索引中的向量数量"""
        # 只添加3个向量
        self.vector_store.add_vectors(self.test_vectors[:3], self.test_ids[:3])
        
        # 请求5个结果
        results = self.vector_store.search_similar(self.query_vector, top_k=5)
        
        # 应该只返回3个结果
        self.assertEqual(len(results), 3)

    def test_save_and_load_index(self):
        """测试保存和加载索引"""
        # 添加数据
        self.vector_store.add_vectors(self.test_vectors, self.test_ids)
        
        # 创建临时目录
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'test.index')
        
        try:
            # 保存索引
            self.vector_store.save_index(temp_path)
            self.assertTrue(os.path.exists(temp_path))
            
            # 创建新的向量存储并加载索引
            new_vector_store = FAISSVectorStore(dimension=self.dimension)
            new_vector_store.load_index(temp_path)
            new_vector_store.ids = self.test_ids.copy()  # 需要手动恢复ids
            
            # 验证加载后的搜索功能
            results_original = self.vector_store.search_similar(self.query_vector)
            results_loaded = new_vector_store.search_similar(self.query_vector)
            
            # 结果应该相同
            self.assertEqual(len(results_original), len(results_loaded))
            for (id1, dist1), (id2, dist2) in zip(results_original, results_loaded):
                self.assertEqual(id1, id2)
                self.assertAlmostEqual(dist1, dist2, places=6)
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_edge_cases(self):
        """测试边界情况"""
        # 空向量列表
        empty_vectors = np.array([], dtype=np.float32).reshape(0, self.dimension)
        self.vector_store.add_vectors(empty_vectors, [])
        self.assertEqual(self.vector_store.index.ntotal, 0)
        
        # 单个向量
        single_vector = np.random.rand(1, self.dimension).astype(np.float32)
        self.vector_store.add_vectors(single_vector, ["single_id"])
        self.assertEqual(self.vector_store.index.ntotal, 1)

    def test_ids_vectors_mismatch(self):
        """测试向量和ID数量不匹配的情况"""
        # 修改测试用例，确保会触发错误
        with self.assertRaises(ValueError):
            # 向量和ID数量不匹配（3个向量，5个ID）
            self.vector_store.add_vectors(self.test_vectors[:3], self.test_ids[:5])

    def test_search_with_2d_query(self):
        """测试使用二维查询向量"""
        self.vector_store.add_vectors(self.test_vectors, self.test_ids)
        
        # 使用二维查询向量
        query_2d = self.query_vector.reshape(1, -1)
        results = self.vector_store.search_similar(query_2d, top_k=3)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIn(result[0], self.test_ids)

if __name__ == '__main__':
    unittest.main()