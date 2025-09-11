from django.db import models
import uuid
import json

class Markdown(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    title = models.TextField(default="[]")  # 将title字段改为TextField以存储标签列表的JSON字符串
    content = models.CharField(max_length=350)
    vector_id = models.CharField(max_length=36, blank=True, null=True)
    number = models.IntegerField()
    word_count = models.IntegerField()
    document_id = models.CharField(max_length=36)
    kb_id = models.CharField(max_length=36, default="0")  # 添加kb_id字段并设置默认值
    creater_id = models.CharField(max_length=36)  # 保持该字段
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # 尝试解析title为标签列表，如果失败则使用原始字符串
        try:
            tags = json.loads(self.title)
            if isinstance(tags, list):
                return f"{'/'.join(tags) if tags else '无标签'} - 第{self.number}段"
        except json.JSONDecodeError:
            pass
        return f"{self.title} - 第{self.number}段"