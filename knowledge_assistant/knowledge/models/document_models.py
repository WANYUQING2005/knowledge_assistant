from django.db import models
import uuid
from .knowledge_base_models import KnowledgeBase  # 新增导入
from .markdown_models import Markdown  # 新增导入

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
     # 重写save方法设置默认creater_id
    def save(self, *args, **kwargs):
        # 仅当creater_id为None时才使用默认值，保留请求传入的空字符串
        if self.creater_id is None:
            self.creater_id = self.get_default_creater_id()
        super().save(*args, **kwargs)

    def split_into_markdowns(self):
        # 获取文档内容（需要您实现_get_document_content方法）
        content = self._get_document_content()
        
        # 新增：将文件内容转换为Markdown格式
        content = self.convert_to_markdown(content)
        # 调用分段策略（当前为300字符固定分段，未来可替换为AI分段）
        chunks = self._split_content_strategy(content)
        
        # 清除现有关联的markdown记录
        Markdown.objects.filter(document_id=self.id).delete()
        
        markdowns = []
        for index, chunk in enumerate(chunks, start=1):
            markdown = Markdown(
                title="123456",
                content=chunk,
                vector_id="",  # 预留AI向量ID字段
                number=index,
                word_count=len(chunk),
                document_id=self.id,
                creater_id=self.creater_id
            )
            markdowns.append(markdown)
        
        Markdown.objects.bulk_create(markdowns)
        self.chunk_count = len(markdowns)
        self.save(update_fields=['chunk_count'])
        
        return markdowns
    
    def _split_content_strategy(self, content):
        """分段策略接口：当前为300字符固定分段，未来可替换为AI智能分段
        Args:
            content: 原始文档内容
        Returns:
            list: 分段后的文本列表
        """
        # 当前实现：300字符固定分段
        chunk_size = 300
        return [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    
    def convert_to_markdown(self, content):
        # 根据文件类型调用不同转换逻辑的预留接口
        # 当前版本直接返回原内容
        file_type = self.file_type.lower()
        
        # 未来可扩展的转换逻辑框架
        # if file_type == 'pdf':
        #     return self._convert_pdf_to_markdown(content)
        # elif file_type in ['cpp', 'java', 'py']:
        #     return self._convert_code_to_markdown(content)
        # ... 其他文件类型转换逻辑
        
        return content