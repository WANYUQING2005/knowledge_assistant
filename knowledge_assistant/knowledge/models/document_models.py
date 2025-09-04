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
    def save(self, *args, **kwargs):
        # 仅当creater_id为None时才使用默认值，保留请求传入的空字符串
        if self.creater_id is None:
            self.creater_id = self.get_default_creater_id()
        
        # 新增：首次保存且文件类型为markdown时触发分段
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 新增：文档创建时自动分段（仅对markdown文件）
        if is_new and self.file_type.lower() == 'markdown':
            self.split_into_markdowns()
    def split_into_markdowns(self):
        # 获取文档内容（已实现_get_document_content方法）
        content = self._get_document_content()
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
    
    # 新增：实现文档内容读取方法
    def _get_document_content(self):
        """从storage_uri读取文档内容"""
        import os
        from django.conf import settings
        
        # 检查文件路径是否存在
        full_path = os.path.join(settings.MEDIA_ROOT, self.storage_uri)
        if not os.path.exists(full_path):
            print(f"文档文件不存在: {full_path}")
            return ""
            
        try:
            with open(full_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"读取文档内容失败: {str(e)}")
            return ""
    
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
    
    