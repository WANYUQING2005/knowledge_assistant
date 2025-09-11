from django.db import models

class RagDocuments(models.Model):
    path = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=512)
    source_type = models.CharField(max_length=64, null=True)
    tags = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class RagChunks(models.Model):
    doc = models.ForeignKey(RagDocuments, on_delete=models.CASCADE, related_name='chunks')
    ord = models.IntegerField()
    content = models.CharField(max_length=350)
    content_hash = models.CharField(max_length=64, unique=True)
    split = models.CharField(max_length=16)
    metadata = models.JSONField(null=True)
    chunk_tags = models.JSONField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tag0 = models.CharField(max_length=64, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['doc', 'ord']),
            models.Index(fields=['tag0']),
            # 暂时移除content索引，稍后将通过自定义迁移添加带长度限制的索引
        ]