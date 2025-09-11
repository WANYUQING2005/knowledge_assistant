from django.db import models
import uuid

class ChatMessage(models.Model):
    id = models.CharField(max_length=36, primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=36)
    user_id = models.CharField(max_length=36)
    kb_id = models.IntegerField(default=0)
    sender = models.CharField(max_length=20, choices=[('user', '用户'), ('ai', 'AI')])
    # 用户要求：直接存储content数据，设置最大长度为10000
    content = models.CharField(max_length=10000)
    create_at = models.DateTimeField(auto_now_add=True)
    # 用户要求：保留chat_number表示是对话中的第几条消息
    chat_number = models.IntegerField()
    # 用于存储消息的元数据
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.sender} - 第{self.chat_number}条消息"