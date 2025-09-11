from django.db import models
import uuid

def generate_knowledge_id():
    return str(uuid.uuid4())

class KnowledgeBase(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=generate_knowledge_id, editable=False)
    owner_user_id = models.CharField(max_length=36)
    name = models.CharField(max_length=100, default="我的知识库")
    description = models.TextField(default="")
    embed_model = models.CharField(max_length=80, default="0")
    create_at = models.DateTimeField(auto_now_add=True)
    # 新增存储大小字段，记录所有markdown内容的总字节数
    storage_size = models.IntegerField(default=0)


    def __str__(self):
        return self.name

    def update_storage_size(self):
        """更新知识库的存储大小，计算所有关联的markdown内容的总字节数"""
        from .markdown_models import Markdown
        
        # 计算所有关联的markdown内容的总字节数
        total_size = sum(
            len(markdown.content.encode('utf-8'))
            for markdown in Markdown.objects.filter(kb_id=self.id)
        )
        
        # 更新存储大小
        self.storage_size = total_size
        self.save(update_fields=['storage_size'])