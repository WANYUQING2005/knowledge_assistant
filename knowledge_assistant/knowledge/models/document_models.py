from django.db import models
import uuid
import hashlib
import logging
from django.db import models
from .knowledge_base_models import KnowledgeBase  # 新增导入
from .markdown_models import Markdown  # 新增导入

# 创建logger对象
logger = logging.getLogger(__name__)

class Document(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    knowledge_base_id = models.CharField(max_length=36)
    title = models.CharField(max_length=200)
    file_type = models.CharField(max_length=40)
    storage_uri = models.CharField(max_length=255)
    chunk_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    # 新增creater_id字段
    creater_id = models.CharField(max_length=36)

    def __str__(self):
        return f"{self.title} ({self.file_type})"

    # 新增方法：获取默认创建者ID（知识库所有者）
    def get_default_creater_id(self):
        try:
            knowledge_base = KnowledgeBase.objects.get(id=self.knowledge_base_id)
            return knowledge_base.owner_user_id
        except KnowledgeBase.DoesNotExist:
            return None

    # 重写save方法设置默认creater_id
    def save(self, *args, **kwargs):
        # 仅当creater_id为None时才使用默认值，保留请求传入的空字符串
        if self.creater_id is None:
            self.creater_id = self.get_default_creater_id()
        
        # 新增：首次保存且文件类型为markdown时触发分段
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 只对markdown类型的文档调用split_into_markdowns方法
        if self.file_type.lower() == 'markdown':
            logger.debug(f"save: is_new={is_new}, file_type={self.file_type}")
            logger.debug(f"save: calling split_into_markdowns for document {self.id}")
            self.split_into_markdowns()
    def split_into_markdowns(self):
        logger.debug(f"split_into_markdowns: starting for document {self.id}")
        # 获取文档内容（已实现_get_document_content方法）
        content = self._get_document_content()
        logger.debug(f"split_into_markdowns: content length={len(content)}")
        
        # 调用分段策略（当前为300字符固定分段，未来可替换为AI分段）
        chunks = self._split_content_strategy(content)
        logger.debug(f"split_into_markdowns: got {len(chunks)} chunks")
        
        # 清除现有关联的markdown记录
        Markdown.objects.filter(document_id=self.id).delete()
        
        markdowns = []
        for index, chunk in enumerate(chunks, start=1):
            # 使用分块返回的第一个标签作为标题，若无标签则使用分块序号
            chunk_tags = chunk[1]
            title = chunk_tags[0] if chunk_tags else f"Chunk {index}"
            markdown = Markdown(
                    title=title,
                    content=chunk[0],
                    vector_id=self._get_vector_id(chunk[0]),  # 从向量数据库获取ID
                    number=index,
                    word_count=len(chunk[0]),
                    document_id=self.id,
                    kb_id=self.knowledge_base_id,  # 设置kb_id字段
                    creater_id=self.creater_id
                )
            markdowns.append(markdown)
        
        Markdown.objects.bulk_create(markdowns)
        self.chunk_count = len(markdowns)
        # 使用super().save直接调用父类的save方法，避免触发当前类的save方法中的循环调用
        super(Document, self).save(update_fields=['chunk_count'])
        logger.debug(f"split_into_markdowns: created {len(markdowns)} markdown records")
        
        return markdowns
    
    # 新增：实现文档内容读取方法
    def _get_document_content(self):
        """从storage_uri读取文档内容"""
        import os
        from django.conf import settings
        
        logger.debug(f"_get_document_content: storage_uri={self.storage_uri}")
        # 检查文件路径是否存在
        full_path = os.path.join(settings.MEDIA_ROOT, self.storage_uri)
        logger.debug(f"_get_document_content: full_path={full_path}")
        if not os.path.exists(full_path):
            logger.error(f"文档文件不存在: {full_path}")
            return ""
            
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
                logger.debug(f"_get_document_content: read {len(content)} characters")
                return content
        except Exception as e:
            logger.error(f"读取文档内容失败: {str(e)}")
            return ""
    
    def _split_content_strategy(self, content):
        """使用LLM进行语义分段的策略
        Args:
            content: 原始文档内容
        Returns:
            list: 分段后的文本列表
        """
        import sys
        from pathlib import Path
        
        # 添加项目根目录到Python路径
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        sys.path.append(str(root_dir))
        
        from rag_demo.llm_chunker import llm_chunk_and_tag, load_tag_candidates
        from rag_demo.ingest import build_engine
        from sqlalchemy import text
        import os
        
        # 加载标签候选词表
        tag_candidates = load_tag_candidates()
        # 设置最大分块字符数（可从环境变量读取或使用默认值）
        max_chunk_chars = int(os.getenv("MAX_CHUNK_CHARS", "300"))
        
        # 从markdown内容中提取标题作为额外标签候选
        import re
        markdown_titles = re.findall(r'^#+\s+(.*)$', content, re.MULTILINE)
        tag_candidates.extend(markdown_titles)

        # 调用LLM分块函数
        documents = llm_chunk_and_tag(
            text=content,
            tag_candidates=tag_candidates,
            max_chunk_chars=max_chunk_chars,
            source=self.storage_uri,
            title=self.title
        )

        # 返回包含内容和标签的元组列表
        return [(doc.page_content, doc.metadata.get('tags', [])) for doc in documents]

    def _get_vector_id(self, content):
        """将内容存入向量数据库并返回向量ID"""
        import os
        from pathlib import Path
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document as LC_Document
        from rag_demo.embeddings_zhipu import ZhipuAIEmbeddingsLC
        import hashlib
        
        # 添加项目根目录到Python路径
        root_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        # 内容哈希作为唯一标识
        content_hash = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
        
        # 初始化嵌入模型
        embeddings = ZhipuAIEmbeddingsLC()
        
        # 索引目录
        index_dir = os.path.join(root_dir, "rag_demo", "index", "faiss")
        
        # 检查并加载现有索引
        if os.path.isdir(index_dir):
            vs = FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)
        else:
            vs = None
            os.makedirs(index_dir, exist_ok=True)
        
        # 创建文档对象，添加kb_id到元数据中
        doc = LC_Document(page_content=content, metadata={"source": self.storage_uri, "title": self.title, "kb_id": self.knowledge_base_id})
        
        # 记录当前索引数量，用于生成新的向量ID
        start_index = vs.index.ntotal if vs else 0
        
        # 添加文档到向量存储
        if vs is None:
            vs = FAISS.from_documents([doc], embeddings)
        else:
            vs.add_documents([doc])
        
        # 保存更新后的索引
        vs.save_local(index_dir)
        
        # 返回新添加文档的向量ID
        vector_id = str(start_index)
        
        # 可以选择不将vector_id存储到MySQL数据库，仅依赖FAISS索引
        return vector_id